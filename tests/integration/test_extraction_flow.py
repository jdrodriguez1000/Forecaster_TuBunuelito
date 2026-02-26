import pytest
import os
import pandas as pd
import datetime
from src.loader import DataLoader
from src.connectors.db_connector import DBConnector
from src.utils.config_loader import load_config
from unittest.mock import patch, MagicMock

class TestExtractionIntegration:
    """
    Pruebas de Integración para el flujo de Extracción y Auditoría.
    Se comunica con Supabase real y valida la persistencia local.
    """

    @classmethod
    def setup_class(cls):
        """Prepara el entorno para pruebas de integración."""
        cls.config = load_config()
        cls.raw_path = cls.config.get("general", {}).get("data_raw_path", "data/01_raw")
        cls.reports_path = os.path.join(
            cls.config.get("general", {}).get("outputs_path", "outputs"),
            "reports/phase_01"
        )
        cls.loader = DataLoader()

    def test_full_extraction_flow_real(self):
        """
        [POSITIVO] Ejecuta una extracción real contra Supabase y valida 
        que se creen los archivos .parquet y el reporte de auditoría.
        """
        # Ejecutar extracción
        report = self.loader.run_extraction()
        
        # 1. Validar reporte consolidado
        assert "phase" in report
        assert report["metrics"]["successful_extractions"] > 0
        assert report["metrics"]["total_tables_processed"] == len(self.config["extractions"]["tables"])
        
        # 2. Validar que los archivos .parquet existan físicamente
        for table in self.config["extractions"]["tables"]:
            file_path = os.path.join(self.raw_path, f"{table}.parquet")
            assert os.path.exists(file_path), f"El archivo parquet para {table} no se creó."
            
            # 3. Leer una muestra del parquet para validar tipos
            df = pd.read_parquet(file_path)
            assert not df.empty
            if "fecha" in df.columns:
                assert pd.api.types.is_datetime64_any_dtype(df["fecha"])

    def test_audit_report_content(self):
        """
        [POSITIVO] Valida que el archivo JSON de auditoría tenga el formato correcto
        y contenga las previsualizaciones solicitadas.
        """
        report_path = os.path.join(self.reports_path, "phase_01_extractions_latest.json")
        assert os.path.exists(report_path)
        
        import json
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # Verificar estructura de auditoría por tabla
        for table, audit in data["table_audits"].items():
            if audit["status"] != "error":
                assert "preview" in audit
                assert "first_3_rows" in audit["preview"]
                assert "last_3_rows" in audit["preview"]
                assert "sample_3_rows" in audit["preview"]
                assert len(audit["preview"]["first_3_rows"]) <= 3

    def test_incremental_logic_simulation(self, tmp_path):
        """
        [NEGATIVO/LÓGICA] Verifica que la lógica incremental detecte correctamente 
        el last_date incluso si forzamos un escenario controlado.
        """
        # Usamos una carpeta temporal para no afectar los datos reales de data/01_raw
        temp_raw = tmp_path / "raw"
        temp_raw.mkdir()
        
        # Crear un archivo parquet 'dummy' con fechas viejas
        table_name = "ventas"
        dummy_file = temp_raw / f"{table_name}.parquet"
        old_data = pd.DataFrame({
            "fecha": pd.to_datetime(["2020-01-01", "2020-01-02"]),
            "unidades_totales": [100, 110]
        })
        old_data.to_parquet(dummy_file)
        
        loader = DataLoader()
        loader.raw_path = str(temp_raw)
        
        # Simular fetch_table para que devuelva solo 1 fila nueva
        new_row = pd.DataFrame({
            "fecha": pd.to_datetime(["2020-01-03"]),
            "unidades_totales": [120]
        })
        
        with patch.object(loader, "_fetch_table", return_value=new_row) as mock_fetch:
            # Solo queremos probar la tabla 'ventas' para este test
            with patch.dict(loader.config["extractions"], {"tables": ["ventas"]}):
                loader.run_extraction()
                
                # Verificar que fetch_table fue llamado con la fecha máxima (2020-01-02)
                called_date = mock_fetch.call_args[1].get("last_date")
                assert called_date == pd.Timestamp("2020-01-02")
                
                # Verificar que el archivo final tenga 3 filas
                df_final = pd.read_parquet(dummy_file)
                assert len(df_final) == 3

    def test_connection_failure_handling(self):
        """
        [NEGATIVO] Verifica que el sistema maneje gracilmente un error de conexión.
        """
        loader = DataLoader()
        # Parchear el cliente de DBConnector para que falle al ejecutar consulta
        with patch.object(loader.db, "get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.table.side_effect = Exception("Conexión rechazada")
            mock_get_client.return_value = mock_client
            
            # Solo una tabla para rapidez
            with patch.dict(loader.config["extractions"], {"tables": ["ventas"]}):
                report = loader.run_extraction()
                
                assert report["metrics"]["failed_extractions"] > 0
                assert "ventas" in report["table_audits"]
                assert report["table_audits"]["ventas"]["status"] == "error"

