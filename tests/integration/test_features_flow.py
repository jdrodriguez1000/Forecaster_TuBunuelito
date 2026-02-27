import unittest
import pandas as pd
import os
import shutil
import yaml
import json
from src.features import FeatureEngineer

class TestFeaturesIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.abspath("tests/temp_features_integ")
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir)
        
        # Mock paths
        self.data_dir = os.path.join(self.test_dir, "data")
        self.outputs_dir = os.path.join(self.test_dir, "outputs")
        os.makedirs(os.path.join(self.data_dir, "02_cleansed"), exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, "04_processed"), exist_ok=True)
        os.makedirs(os.path.join(self.outputs_dir, "reports/phase_04"), exist_ok=True)
        os.makedirs(os.path.join(self.outputs_dir, "figures/phase_04"), exist_ok=True)

        self.config_path = os.path.join(self.test_dir, "config.yaml")
        self.config_dict = {
            "general": {
                "outputs_path": self.outputs_dir.replace('\\', '/'),
                "data_processed_path": os.path.join(self.data_dir, "04_processed").replace('\\', '/'),
                "random_state": 42
            },
            "eda": {
                "target_variable": "target",
                "business_rules": {
                    "payments": {"quincenas": [15, 30], "prima_legal": {"june": [15, 20], "december": [15, 20]}},
                    "events": {
                        "novenas": {"month": 12, "days": [16, 26]},
                        "feria_flores": {"month": 8, "days": [1, 10]}
                    }
                }
            },
            "features": {
                "transformations": {
                    "exogenous_lags": {"trm": 30},
                    "momentum": {"ipc_lookback_days": 90},
                    "clima": {"persistence_window": 3, "heavy_rain_threshold": "fuerte"}
                },
                "interactions": [
                    ["es_promocion", "is_sunday"],
                    ["es_quincena", "is_heavy_rain"]
                ],
                "drop_columns": ["unnecessary_col"]
            }
        }
        with open(self.config_path, "w", encoding='utf-8') as f:
            yaml.dump(self.config_dict, f)

        # Crear data de entrada (cleansed)
        self.input_path = os.path.join(self.data_dir, "02_cleansed/master_data.parquet")
        self.mock_data = pd.DataFrame({
            "fecha": pd.date_range("2023-01-01", periods=100),
            "target": range(100),
            "unnecessary_col": [0]*100,
            "trm": [4000]*100,
            "inflacion_mensual_ipc": [0.5]*100,
            "es_dia_lluvioso": [0]*100,
            "tipo_lluvia": ["no"]*100,
            "precio_unitario": [2500]*100,
            "smlv": [1300000]*100,
            "es_promocion": [0]*100,
            "costo_unitario": [1000]*100
        })
        self.mock_data.to_parquet(self.input_path)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_full_features_flow(self):
        """Prueba de integración: del cleansed al processed con reporte y figuras."""
        fe = FeatureEngineer(config_path=self.config_path)
        # Patch outputs path manually as constructor might use defaults if not careful
        fe.outputs_path = os.path.join(self.data_dir, "04_processed")
        
        df_result = fe.run_pipeline(self.mock_data)
        
        # 1. Verificar persistencia del dataset
        latest_parquet = os.path.join(self.data_dir, "04_processed/dataset_features_latest.parquet")
        self.assertTrue(os.path.exists(latest_parquet))
        
        # 2. Verificar reporte JSON
        report_file = os.path.join(self.outputs_dir, "reports/phase_04/phase_04_features_latest.json")
        self.assertTrue(os.path.exists(report_file))
        
        with open(report_file, 'r', encoding='utf-8') as f:
            report = json.load(f)
            
        self.assertEqual(report["phase"], "04_feature_engineering")
        self.assertIn("quality_audit", report)
        self.assertIn("vif_analysis", report["quality_audit"]["statistical_diagnostics"])
        
        # 3. Verificar figuras
        fig_file = os.path.join(self.outputs_dir, "figures/phase_04/correlation_matrix_latest.png")
        self.assertTrue(os.path.exists(fig_file))
        
        # 4. Verificar lógica de negocio aplicada (ej. columnas creadas)
        self.assertIn("es_quincena", df_result.columns)
        self.assertIn("interaction_es_promocion_is_sunday", df_result.columns)
        self.assertNotIn("unnecessary_col", df_result.columns)

if __name__ == "__main__":
    unittest.main()
