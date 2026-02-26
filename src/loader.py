import os
import pandas as pd
import numpy as np
import logging
import datetime
from typing import Dict, Any, List, Optional
from src.connectors.db_connector import DBConnector
from src.utils.auditor import DataAuditor
from src.utils.config_loader import load_config
from src.utils.helpers import save_report

logger = logging.getLogger(__name__)

class DataLoader:
    """
    Orquestador de la Fase 01: Extractions.
    Responsable de descargar datos de Supabase de forma incremental, ejecutar auditorías de calidad
    y persistir los resultados localmente en formato Parquet siguiendo el protocolo de dual persistencia.
    """

    def __init__(self):
        self.config = load_config()
        self.db = DBConnector()
        self.auditor = DataAuditor()
        
        # Rutas desde config
        self.raw_path = self.config.get("general", {}).get("data_raw_path", "data/01_raw")
        self.reports_path = os.path.join(
            self.config.get("general", {}).get("outputs_path", "outputs"),
            "reports/phase_01"
        )
        
        os.makedirs(self.raw_path, exist_ok=True)
        os.makedirs(self.reports_path, exist_ok=True)

    def run_extraction(self) -> Dict[str, Any]:
        """
        Ejecuta el proceso completo de extracción (incremental) para todas las tablas configuradas.
        """
        tables = self.config.get("extractions", {}).get("tables", [])
        phase_report = {
            "phase": "01_extractions",
            "timestamp": datetime.datetime.now().isoformat(),
            "description": "Reporte consolidado de extracción incremental y auditoría de datos",
            "metrics": {
                "total_tables_processed": 0,
                "successful_extractions": 0,
                "failed_extractions": 0,
                "total_rows_extracted": 0,
                "incremental_updates": 0,
                "full_extractions": 0
            },
            "table_audits": {}
        }

        logger.info(f"Iniciando extracción de {len(tables)} tablas en formato Parquet...")

        for table in tables:
            phase_report["metrics"]["total_tables_processed"] += 1
            try:
                file_path = os.path.join(self.raw_path, f"{table}.parquet")
                df_existing = pd.DataFrame()
                last_date = None

                # 1. Cargar datos existentes si el archivo existe
                if os.path.exists(file_path):
                    logger.info(f"Archivo existente encontrado para '{table}'. Cargando para extracción incremental.")
                    df_existing = pd.read_parquet(file_path)
                    if not df_existing.empty and "fecha" in df_existing.columns:
                        # Asegurar tipo datetime
                        df_existing["fecha"] = pd.to_datetime(df_existing["fecha"])
                        last_date = df_existing["fecha"].max()
                        phase_report["metrics"]["incremental_updates"] += 1
                    else:
                        phase_report["metrics"]["full_extractions"] += 1
                else:
                    logger.info(f"No hay archivo local para '{table}'. Iniciando extracción completa.")
                    phase_report["metrics"]["full_extractions"] += 1

                # 2. Descargar nuevos datos (con paginación y filtro incremental)
                df_new = self._fetch_table(table, last_date=last_date)
                
                if df_new.empty:
                    logger.info(f"No hay registros nuevos para la tabla '{table}'.")
                    df_final = df_existing
                else:
                    # Combinar datos
                    df_final = pd.concat([df_existing, df_new], ignore_index=True)
                    # Eliminar duplicados si existen (por fecha si aplica)
                    if "fecha" in df_final.columns:
                        df_final = df_final.drop_duplicates(subset=["fecha"], keep="last")
                    
                    # Persistencia Local (Formato Parquet)
                    df_final.to_parquet(file_path, index=False, engine="pyarrow")
                    logger.info(f"Tabla '{table}' actualizada y guardada en {file_path}")

                # 3. Ejecutar Auditoría (Abogado del Diablo)
                audit_results = self.auditor.audit_dataframe(df_final, table)
                
                # 4. Generar Vista Previa (Preview)
                audit_results["preview"] = self._get_preview(df_final)
                
                phase_report["table_audits"][table] = {
                    "status": "success",
                    "audit_details": audit_results,
                    "preview": audit_results.get("preview", {})
                }
                
                # Actualizar métricas globales
                phase_report["metrics"]["total_rows_extracted"] += df_new.shape[0]
                phase_report["metrics"]["successful_extractions"] += 1

            except Exception as e:
                logger.error(f"Error procesando tabla '{table}': {str(e)}", exc_info=True)
                phase_report["metrics"]["failed_extractions"] += 1
                phase_report["table_audits"][table] = {
                    "status": "error",
                    "error_message": str(e)
                }

        # Guardar Reporte Final (Protoclo Dual Persistencia con soporte UTF-8 via helper)
        save_report(phase_report, "phase_01_extractions", outputs_path=self.reports_path)
        
        return phase_report

    def _fetch_table(self, table_name: str, last_date: Optional[datetime.datetime] = None) -> pd.DataFrame:
        """
        Descarga datos de Supabase manejando el límite de 1000 registros mediante paginación.
        Si se provee last_date, solo descarga registros con fecha > last_date.
        """
        client = self.db.get_client()
        all_data = []
        page_size = 1000
        offset = 0
        
        logger.info(f"Consultando Supabase para '{table_name}'...")
        
        while True:
            query = client.table(table_name).select("*").range(offset, offset + page_size - 1)
            
            # Aplicar filtro incremental si existe
            if last_date:
                # El formato de fecha debe ser compatible con Supabase (ISO)
                last_date_str = last_date.strftime("%Y-%m-%d")
                query = query.gt("fecha", last_date_str)
                logger.info(f"Filtro incremental activo: fecha > {last_date_str}")

            response = query.execute()
            data = response.data
            
            if not data:
                break
                
            all_data.extend(data)
            
            # Si trajimos menos que el page_size, terminamos
            if len(data) < page_size:
                break
            
            offset += page_size
            logger.info(f"Descargados {len(all_data)} registros de '{table_name}'...")

        if not all_data:
            return pd.DataFrame()
            
        df = pd.DataFrame(all_data)
        if "fecha" in df.columns:
            df["fecha"] = pd.to_datetime(df["fecha"])
            
        return df

    def _get_preview(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Genera una previsualización de los datos: 3 primeras, 3 últimas y 3 aleatorias.
        """
        if df.empty:
            return {"message": "El DataFrame está vacío"}

        # Convertir a dict para que sea JSON serializable
        def to_json_dict(sub_df):
            # Formatear fechas para mejor visualización en el JSON
            for col in sub_df.select_dtypes(include=['datetime64']).columns:
                sub_df[col] = sub_df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
            return sub_df.astype(object).to_dict(orient="records")

        preview = {
            "first_3_rows": to_json_dict(df.head(3).copy()),
            "last_3_rows": to_json_dict(df.tail(3).copy()),
            "sample_3_rows": to_json_dict(df.sample(min(3, len(df)), random_state=42).copy())
        }
        
        return preview

if __name__ == "__main__":
    # Script de prueba rápida para el componente
    logging.basicConfig(level=logging.INFO)
    loader = DataLoader()
    results = loader.run_extraction()
    print("Proceso de extracción finalizado con éxito.")
