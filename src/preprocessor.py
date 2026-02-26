import os
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Any
from src.utils.config_loader import load_config
from src.utils.auditor import DataAuditor
from src.utils.helpers import save_report

logger = logging.getLogger(__name__)

class DataPreprocessor:
    """
    Clase encargada de la Fase 02: Preprocessing.
    Implementa la limpieza de integridad, manejo de duplicados, alineación de contratos
    y reindexación temporal diaria.
    """

    def __init__(self, config_path: str = "config.yaml"):
        self.config = load_config(config_path)
        self.raw_path = self.config['general']['data_raw_path']
        self.cleansed_path = self.config['general']['data_cleansed_path']
        self.reports_path = os.path.join(self.config['general']['outputs_path'], "reports/phase_02")
        self.schemas = self.config['extractions']['schemas']
        self.sentinels = self.config['extractions']['sentinel_values']
        
        # Asegurar directorio de salida
        os.makedirs(self.cleansed_path, exist_ok=True)

    def run(self) -> Dict[str, Any]:
        """
        Ejecuta el flujo de preprocesamiento para todas las tablas configuradas.
        """
        logger.info("Iniciando Fase 02: Preprocessing (Integridad y Limpieza)")
        
        phase_report = {
            "phase": "02_preprocessing",
            "timestamp": pd.Timestamp.now().isoformat(),
            "description": "Limpieza de integridad, deduplicación y reindexación diaria",
            "table_reports": {}
        }
        
        tables = self.config['extractions']['tables']
        
        for table in tables:
            try:
                # 1. Cargar data raw
                file_path = os.path.join(self.raw_path, f"{table}.parquet")
                if not os.path.exists(file_path):
                    logger.warning(f"Archivo raw no encontrado para la tabla: {table}")
                    continue
                
                df = pd.read_parquet(file_path)
                initial_shape = df.shape
                
                # 2. Aplicar limpieza de integridad
                df_cleansed, audit_log = self._clean_table(df, table)
                
                # 3. Guardar en cleansed
                output_file = os.path.join(self.cleansed_path, f"{table}.parquet")
                df_cleansed.to_parquet(output_file, index=False)
                
                phase_report["table_reports"][table] = {
                    "status": "success",
                    "initial_shape": initial_shape,
                    "final_shape": df_cleansed.shape,
                    "audit_log": audit_log
                }
                logger.info(f"Tabla '{table}' preprocesada exitosamente.")
                
            except Exception as e:
                logger.error(f"Error preprocesando tabla '{table}': {str(e)}")
                phase_report["table_reports"][table] = {
                    "status": "error",
                    "error_message": str(e)
                }
        
        # 4. Merge Maestro (Consolidación)
        try:
            master_report = self._merge_master(phase_report["table_reports"])
            phase_report["master_audit"] = master_report
            logger.info("Merge Maestro completado exitosamente.")
        except Exception as e:
            logger.error(f"Error en el Merge Maestro: {str(e)}")
            phase_report["master_audit"] = {"status": "error", "message": str(e)}

        # Guardar Reporte Final
        save_report(phase_report, "phase_02_preprocessing", outputs_path=self.reports_path)
        
        return phase_report

    def _merge_master(self, table_reports: Dict[str, Any]) -> Dict[str, Any]:
        """
        Une todas las tablas preprocesadas en un solo dataset maestro.
        """
        dfs = []
        for table, report in table_reports.items():
            if report.get("status") == "success":
                file_path = os.path.join(self.cleansed_path, f"{table}.parquet")
                dfs.append(pd.read_parquet(file_path))
        
        if not dfs:
            raise ValueError("No hay tablas preprocesadas exitosamente para unir.")
        
        # Merge secuencial por fecha
        master_df = dfs[0]
        for next_df in dfs[1:]:
            # Usamos inner merge ya que todas fueron reindexadas al mismo rango
            master_df = pd.merge(master_df, next_df, on='fecha', how='inner')
        
        # Establecer la fecha como índice (Punto Crítico para Series de Tiempo)
        master_df = master_df.set_index('fecha')
        
        # Guardar Master Data
        master_output = os.path.join(self.cleansed_path, "master_data.parquet")
        master_df.to_parquet(master_output, index=True) # index=True para conservar el índice de fecha
        
        # Auditoría del Master
        audit = {
            "total_rows": len(master_df),
            "total_columns": len(master_df.columns),
            "columns_info": {col: str(dtype) for col, dtype in master_df.dtypes.items()},
            "null_values_count": int(master_df.isnull().sum().sum()),
            "duplicate_rows": int(master_df.duplicated().sum()),
            "duplicate_columns": int(len(master_df.columns) - len(set(master_df.columns))),
            "index_name": str(master_df.index.name),
            "date_range": {
                "start": master_df.index.min().isoformat(),
                "end": master_df.index.max().isoformat()
            }
        }
        
        return audit

    def _clean_table(self, df: pd.DataFrame, table_name: str) -> (pd.DataFrame, Dict[str, Any]):
        """
        Aplica los 6 puntos de limpieza definidos por el usuario.
        """
        audit_log = {}
        schema = self.schemas.get(table_name, {})
        valid_cols = list(schema.keys())
        
        # PANTALLAZO INICIAL
        audit_log["initial_rows"] = len(df)

        # 1. Manejo de Centinelas (Punto 6)
        all_sentinels = []
        for v in self.sentinels.values():
            all_sentinels.extend(v)
        
        # Reemplazar valores exactos
        df = df.replace(all_sentinels, np.nan)
        
        # 2. Eliminación de filas repetidas (deja el último registro) (Punto 2)
        rows_before = len(df)
        df = df.drop_duplicates(keep='last')
        audit_log["exact_duplicates_removed"] = rows_before - len(df)

        # 3. Eliminación de columnas fuera de contrato (Punto 3)
        cols_before = set(df.columns)
        actual_valid_cols = [c for c in valid_cols if c in df.columns]
        df = df[actual_valid_cols]
        audit_log["removed_columns"] = list(cols_before - set(actual_valid_cols))

        # 4. Manejo de fechas duplicadas (deja el último registro oficial) (Punto 4)
        if 'fecha' in df.columns:
            df['fecha'] = pd.to_datetime(df['fecha'])
            df = df.sort_values('fecha')
            rows_before = len(df)
            df = df.groupby('fecha').tail(1)
            audit_log["duplicate_dates_removed"] = rows_before - len(df)

            # --- AJUSTES DE REGLAS DE NEGOCIO (Puntos 7 al 11) ---
            if table_name == "ventas":
                # Punto 7 y 8: Unidades en Promoción (2x1)
                if all(c in df.columns for c in ["es_promocion", "unidades_pagas", "unidades_bonificadas"]):
                    # Solo aplicamos el ajuste de bonificadas = pagas en días de promoción
                    promo_mask = df["es_promocion"] == 1
                    diff_mask = df["unidades_pagas"] != df["unidades_bonificadas"]
                    fix_mask = promo_mask & diff_mask
                    
                    df.loc[fix_mask, "unidades_bonificadas"] = df.loc[fix_mask, "unidades_pagas"]
                    audit_log["ajustes_bonificadas_promocion"] = int(fix_mask.sum())
                    
                    # Punto 8: Recalcular totales para asegurar consistencia
                    df["unidades_totales"] = df["unidades_pagas"] + df["unidades_bonificadas"]

            if table_name == "inventario":
                # Punto 9, 10 y 11: Balance de Inventario y Ventas Reales
                cols_inv_needed = ["ventas_reales_pagas", "ventas_reales_bonificadas", "buñuelos_preparados"]
                if all(c in df.columns for c in cols_inv_needed):
                    # Flag de promo por fecha (Abr-May / Sep-Oct, >= 2022) según Regla de Oro
                    m = df["fecha"].dt.month
                    y = df["fecha"].dt.year
                    is_promo = (y >= 2022) & (m.isin([4, 5, 9, 10]))
                    
                    diff_mask = df["ventas_reales_pagas"] != df["ventas_reales_bonificadas"]
                    fix_mask = is_promo & diff_mask
                    
                    # Punto 9: Ajuste de bonificadas
                    df.loc[fix_mask, "ventas_reales_bonificadas"] = df.loc[fix_mask, "ventas_reales_pagas"]
                    audit_log["ajustes_ventas_bonificadas_promocion"] = int(fix_mask.sum())
                    
                    # Punto 10: Actualizar ventas reales totales
                    df["ventas_reales_totales"] = df["ventas_reales_pagas"] + df["ventas_reales_bonificadas"]
                    
                    # Punto 11: Actualizar desperdicios
                    df["buñuelos_desperdiciados"] = df["buñuelos_preparados"] - df["ventas_reales_totales"]

                    # Punto 12: Recalcular demanda_teorica_total (Verdad Absoluta)
                    # La demanda real es lo que se vendió más lo que faltó por vender (agotados)
                    if "unidades_agotadas" in df.columns:
                        # Identificar inconsistencias antes de corregir (para el reporte)
                        expected_demand = df["ventas_reales_totales"] + df["unidades_agotadas"]
                        inconsistencies_mask = df["demanda_teorica_total"] != expected_demand
                        
                        audit_log["correccion_demanda_inconsistente"] = int(inconsistencies_mask.sum())
                        
                        # Aplicar el recálculo a toda la serie para asegurar uniformidad
                        df["demanda_teorica_total"] = expected_demand

            # 5. Llenado de huecos / Continuidad Temporal (Punto 5)
            # Determinar rango completo
            min_date = df['fecha'].min()
            max_date = df['fecha'].max()
            
            if pd.notnull(min_date) and pd.notnull(max_date):
                full_range = pd.date_range(start=min_date, end=max_date, freq='D')
                df = df.set_index('fecha').reindex(full_range).reset_index()
                df = df.rename(columns={'index': 'fecha'})
                audit_log["gaps_filled"] = len(full_range) - len(full_range) # Esto es solo informativo
                audit_log["total_days_final"] = len(df)

            # --- IMPUTACIONES ESPECÍFICAS POR TABLA (Puntos 1 al 4 del clima) ---
            if table_name == "clima":
                # Punto 1: Imputación numérica (ffill -> bfill)
                cols_weather = ["temperatura_media", "probabilidad_lluvia", "precipitacion_mm"]
                for col in [c for c in cols_weather if c in df.columns]:
                    df[col] = df[col].ffill().bfill()
                
                # Punto 2: Imputación categórica (Moda/Ninguna)
                if "tipo_lluvia" in df.columns:
                    # Intentamos calcular la moda, sino usamos 'Ninguna'
                    mode_series = df["tipo_lluvia"].mode()
                    mode_val = mode_series[0] if not mode_series.empty else "Ninguna"
                    df["tipo_lluvia"] = df["tipo_lluvia"].fillna(mode_val)
                
                # Punto 3: Actualizar es_dia_lluvioso basado en tipo_lluvia
                if "tipo_lluvia" in df.columns and "es_dia_lluvioso" in df.columns:
                    df["es_dia_lluvioso"] = df["tipo_lluvia"].apply(lambda x: 0 if x == "Ninguna" else 1)
                
                # Punto 4: Imputación evento_macro (valor anterior)
                if "evento_macro" in df.columns:
                    df["evento_macro"] = df["evento_macro"].ffill()
                    # Si el primer valor es nulo, bfill para evitar NaNs iniciales (opcional pero recomendado)
                    df["evento_macro"] = df["evento_macro"].bfill()

            if table_name == "finanzas":
                # Punto 1: Imputación de precio y costo
                fin_cols = ["precio_unitario", "costo_unitario"]
                if all(c in df.columns for c in fin_cols):
                    # Aplicamos ffill primero para que los 1 de enero (y otros) tomen el valor anterior
                    # Luego bfill para cubrir el inicio de la serie
                    df[fin_cols] = df[fin_cols].ffill().bfill()
                
                # Punto 2: Recálculo de márgenes
                if all(c in df.columns for c in ["precio_unitario", "costo_unitario"]):
                    df["margen_bruto"] = df["precio_unitario"] - df["costo_unitario"]
                    # Evitar división por cero
                    df["porcentaje_margen"] = np.where(df["precio_unitario"] != 0, 
                                                     df["margen_bruto"] / df["precio_unitario"], 
                                                     0)

            if table_name == "macroeconomia":
                # Punto 1: Imputación Forward Fill (prioridad) -> Backward Fill
                df = df.ffill().bfill()

            if table_name == "marketing":
                # Punto 1: Imputación de costos (ffill -> bfill)
                mkt_cols = ["ig_cost", "fb_cost"]
                if all(c in df.columns for c in mkt_cols):
                    df[mkt_cols] = df[mkt_cols].ffill().bfill()
                
                # Punto 2: Campaña activa (1 si hay inversión > 0)
                if all(c in df.columns for c in ["ig_cost", "fb_cost", "campaña_activa"]):
                    df["campaña_activa"] = ((df["ig_cost"] > 0) | (df["fb_cost"] > 0)).astype(int)
                
                # Punto 3: Inversión total
                if all(c in df.columns for c in ["ig_cost", "fb_cost"]):
                    df["inversion_total"] = df["ig_cost"] + df["fb_cost"]
                
                # Punto 4: Porcentajes de inversión (evitando división por cero)
                if "inversion_total" in df.columns:
                    if "ig_cost" in df.columns:
                        df["ig_pct"] = np.where(df["inversion_total"] != 0, 
                                               df["ig_cost"] / df["inversion_total"], 
                                               0)
                    if "fb_cost" in df.columns:
                        df["fb_pct"] = np.where(df["inversion_total"] != 0, 
                                               df["fb_cost"] / df["inversion_total"], 
                                               0)

        # VERIFICACIÓN FINAL DE CALIDAD
        audit_log["valores_nulos_finales"] = int(df.isnull().sum().sum())

        return df, audit_log
