import unittest
import pandas as pd
import numpy as np
import os
import shutil
import yaml
from src.features import FeatureEngineer

class TestFeatureEngineer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Directorio temporal para pruebas
        cls.test_dir = os.path.abspath("tests/temp_features")
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)
        os.makedirs(cls.test_dir, exist_ok=True)
        os.makedirs(os.path.join(cls.test_dir, "processed"), exist_ok=True)
        
        # Mock de configuración mínima
        cls.config_path = os.path.join(cls.test_dir, "test_config.yaml")
        with open(cls.config_path, "w", encoding='utf-8') as f:
            f.write(f"""
general:
  data_processed_path: "{cls.test_dir.replace('\\', '/')}/processed"
  outputs_path: "{cls.test_dir.replace('\\', '/')}/outputs"

eda:
  business_rules:
    payments:
      quincenas: [15, 16, 30, 31]
      prima_legal:
        june: [15, 20]
        december: [15, 20]
    events:
      novenas:
        month: 12
        days: [16, 26]
      feria_flores:
        month: 8
        days: [1, 10]

features:
  target_variable: "demanda_teorica_total"
  drop_columns: ["unidades_totales"]
  transformations:
    exogenous_lags:
      trm: 2
    momentum:
      ipc_lookback_days: 2
    clima:
      persistence_window: 2
      heavy_rain_threshold: "fuerte"
  interactions:
    - ["es_promocion", "is_sunday"]
    - ["es_quincena", "is_heavy_rain"]
            """)
        
        cls.fe = FeatureEngineer(config_path=cls.config_path)

    @classmethod
    def tearDownClass(cls):
        # Limpiar archivos temporales
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)

    def test_calendar_features(self):
        """Verifica la creación correcta de variables de calendario y negocio."""
        data = {
            "fecha": ["2023-01-15", "2023-06-18", "2023-12-24", "2023-08-05", "2023-01-01"]
        }
        df = pd.DataFrame(data)
        df_out = self.fe._create_calendar_features(df)
        
        # Quincena (Enero 15)
        self.assertEqual(df_out.iloc[0]["es_quincena"], 1)
        # Prima Legal (Junio 18)
        self.assertEqual(df_out.iloc[1]["es_prima_legal"], 1)
        # Novena y Domingo (Diciembre 24, 2023 fue Domingo)
        self.assertEqual(df_out.iloc[2]["es_novena"], 1)
        self.assertEqual(df_out.iloc[2]["is_sunday"], 1)
        # Feria de Flores (Agosto 5)
        self.assertEqual(df_out.iloc[3]["es_feria_flores"], 1)
        # No especial (Enero 1)
        self.assertEqual(df_out.iloc[4]["es_quincena"], 0)
        self.assertEqual(df_out.iloc[4]["es_prima_legal"], 0)

    def test_exogenous_transformations(self):
        """Verifica lags, momentum y señales climáticas."""
        data = {
            "trm": [100, 110, 120, 130],
            "inflacion_mensual_ipc": [3.0, 3.1, 3.2, 3.3],
            "es_dia_lluvioso": [0, 1, 1, 0],
            "tipo_lluvia": ["none", "ligera", "fuerte", "none"]
        }
        df = pd.DataFrame(data)
        df_out = self.fe._apply_exogenous_transformations(df)
        
        # Lag TRM (lag=2 en test_config)
        self.assertEqual(df_out.iloc[2]["trm_lag_2"], 100)
        
        # Momentum IPC (lookback=2)
        # 3.2 - 3.0 = 0.2
        self.assertAlmostEqual(df_out.iloc[2]["ipc_momentum"], 0.2)
        
        # Rolling Rain (window=2, shift 1)
        # En idx 2, suma de idx 0 y 1: 0 + 1 = 1
        self.assertEqual(df_out.iloc[2]["rolling_rain_days_3"], 1)
        
        # Heavy Rain Signal
        self.assertEqual(df_out.iloc[2]["is_heavy_rain"], 1)
        self.assertEqual(df_out.iloc[1]["is_light_rain"], 1)

    def test_simulation_ratios(self):
        """Verifica el cálculo de ratios estratégicos."""
        data = {
            "precio_unitario": [1000, 1100],
            "smlv": [300000, 300000],
            "inflacion_mensual_ipc": [10.0, 10.0],
            "costo_unitario": [500, 550],
            "trm_lag_30": [4000, 4000]
        }
        df = pd.DataFrame(data)
        df_out = self.fe._create_simulation_ratios(df)
        
        # Asequibilidad: 1000 / (300000/30) = 1000 / 10000 = 0.1
        self.assertEqual(df_out.iloc[0]["asequibilidad_idx"], 0.1)
        
        # Spread Inflación (Variación precio 10% - IPC 10% = 0)
        self.assertAlmostEqual(df_out.iloc[1]["spread_inflacion"], 0.0)
        
        # Vulnerabilidad TRM: 500 / (4000+1)
        self.assertAlmostEqual(df_out.iloc[0]["vulnerability_trm"], 500/4001)

    def test_interactions(self):
        """Verifica la creación de interacciones."""
        data = {
            "es_promocion": [1, 0, 1],
            "is_sunday": [1, 1, 0],
            "es_quincena": [1, 1, 1],
            "is_heavy_rain": [0, 1, 0]
        }
        df = pd.DataFrame(data)
        df_out = self.fe._create_interactions(df)
        
        self.assertEqual(df_out.iloc[0]["interaction_es_promocion_is_sunday"], 1)
        self.assertEqual(df_out.iloc[1]["interaction_es_quincena_is_heavy_rain"], 1)
        self.assertEqual(df_out.iloc[2]["interaction_es_promocion_is_sunday"], 0)

    def test_run_pipeline_integration(self):
        """Verifica la ejecución completa del pipeline."""
        # Necesitamos suficientes datos para que los lags no dejen el df vacío
        data = {
            "fecha": pd.date_range(start="2023-01-01", periods=10).strftime("%Y-%m-%d"),
            "trm": [100]*10,
            "inflacion_mensual_ipc": [3.0]*10,
            "es_dia_lluvioso": [0]*10,
            "tipo_lluvia": ["none"]*10,
            "precio_unitario": [1000]*10,
            "smlv": [300000]*10,
            "costo_unitario": [500]*10,
            "es_promocion": [0]*10,
            "unidades_totales": [100]*10, # Esta se debe eliminar
            "demanda_teorica_total": [50]*10
        }
        df = pd.DataFrame(data)
        df_out = self.fe.run_pipeline(df)
        
        # 1. Verificar que unidades_totales fue eliminada
        self.assertNotIn("unidades_totales", df_out.columns)
        # 2. Verificar que se crearon nuevas columnas
        self.assertIn("asequibilidad_idx", df_out.columns)
        # 3. Verificar que se eliminaron nulos (df_out será más pequeño por lags)
        # trm_lag_2 y momentum_2 quitan 2 filas
        self.assertEqual(len(df_out), 8)
        # 4. Verificar que se generó el reporte
        report_path = os.path.join(self.test_dir, "outputs", "reports", "phase_04", "phase_04_features_latest.json")
        self.assertTrue(os.path.exists(report_path))

if __name__ == "__main__":
    unittest.main()
