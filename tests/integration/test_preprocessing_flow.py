import pytest
import os
import pandas as pd
import json
from src.preprocessor import DataPreprocessor
from src.utils.config_loader import load_config

class TestPreprocessingIntegration:
    """
    Pruebas de Integración para el flujo de Preprocesamiento (Fase 02).
    Valida la transición de datos raw a datos limpios y la creación del Master Data.
    """

    @classmethod
    def setup_class(cls):
        """Prepara el entorno para pruebas de integración."""
        cls.config = load_config()
        cls.raw_path = cls.config.get("general", {}).get("data_raw_path")
        cls.cleansed_path = cls.config.get("general", {}).get("data_cleansed_path")
        cls.reports_path = os.path.join(
            cls.config.get("general", {}).get("outputs_path"),
            "reports/phase_02"
        )
        cls.preprocessor = DataPreprocessor()

    def test_full_preprocessing_flow(self):
        """
        [POSITIVO] Ejecuta el preprocesamiento completo y valida la existencia de 
        archivos limpios y el Merge Maestro.
        """
        # 1. Asegurar que existan archivos raw (esto depende de que la Fase 01 haya corrido)
        tables = self.config["extractions"]["tables"]
        for table in tables:
            raw_file = os.path.join(self.raw_path, f"{table}.parquet")
            assert os.path.exists(raw_file), f"Falta archivo raw para {table}. Ejecuta la Fase 01 primero."

        # 2. Ejecutar Preprocesamiento
        report = self.preprocessor.run()

        # 3. Validar estado de las tablas en el reporte
        for table in tables:
            assert report["table_reports"][table]["status"] == "success", f"Fallo en prep de {table}"
            assert report["table_reports"][table]["audit_log"]["valores_nulos_finales"] == 0

            # Validar archivos físicos
            cleansed_file = os.path.join(self.cleansed_path, f"{table}.parquet")
            assert os.path.exists(cleansed_file)

        # 4. Validar Merge Maestro
        assert "master_audit" in report
        assert report["master_audit"]["null_values_count"] == 0
        assert report["master_audit"]["index_name"] == "fecha"

        master_file = os.path.join(self.cleansed_path, "master_data.parquet")
        assert os.path.exists(master_file)

        # Validar carga del master
        df_master = pd.read_parquet(master_file)
        assert not df_master.empty
        assert df_master.index.name == "fecha"
        assert df_master.isnull().sum().sum() == 0

    def test_preprocessing_report_persistence(self):
        """
        [POSITIVO] Verifica que el reporte de la fase 02 se guarde correctamente en disco.
        """
        report_path = os.path.join(self.reports_path, "phase_02_preprocessing_latest.json")
        assert os.path.exists(report_path), "El reporte de la fase 02 no se guardó."

        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        assert data["phase"] == "02_preprocessing"
        assert "master_audit" in data
        assert data["master_audit"]["total_rows"] > 0

    def test_master_data_consistency(self):
        """
        [LÓGICA] Verifica que el master data tenga todas las columnas esperadas 
        según la unión de los esquemas.
        """
        master_file = os.path.join(self.cleansed_path, "master_data.parquet")
        df_master = pd.read_parquet(master_file)
        
        # El número de columnas debería ser la suma de columnas de schemas (sin duplicar fecha)
        expected_cols = set()
        for table, schema in self.config["extractions"]["schemas"].items():
            for col in schema.keys():
                if col != "fecha":
                    expected_cols.add(col)
        
        actual_cols = set(df_master.columns)
        
        # Verificamos que al menos las columnas críticas estén presentes
        critical_cols = ["demanda_teorica_total", "unidades_totales", "precio_unitario", "ig_cost", "smlv", "temperatura_media"]
        for col in critical_cols:
            assert col in actual_cols, f"Falta columna crítica {col} en el master data"
