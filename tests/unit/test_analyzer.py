import unittest
import pandas as pd
import numpy as np
import os
import shutil
import yaml
from datetime import datetime
from src.analyzer import DataAnalyzer

class TestDataAnalyzer(unittest.TestCase):
    def setUp(self):
        # Directorio temporal para pruebas
        self.test_dir = os.path.abspath(f"tests/temp_analyzer_{id(self)}")
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir, exist_ok=True)
        
        self.data_dir = os.path.join(self.test_dir, "data_cleansed")
        self.outputs_dir = os.path.join(self.test_dir, "outputs")
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.outputs_dir, exist_ok=True)

        # Mock de configuración
        self.config_path = os.path.join(self.test_dir, "test_config.yaml")
        self.config_dict = {
            "general": {
                "outputs_path": self.outputs_dir.replace('\\', '/'),
                "data_cleansed_path": self.data_dir.replace('\\', '/'),
                "random_state": 42
            },
            "eda": {
                "target_variable": "target",
                "splits": {
                    "test_days": 10,
                    "val_days": 10
                },
                "time_series": {
                    "lags_acf_pacf": 10
                },
                "statistics": {
                    "vif_columns": ["exog1", "exog2"]
                },
                "business_rules": {
                    "payments": {"quincenas": [15, 30]},
                    "events": {
                        "novenas": {"month": 12, "days": [16, 24]},
                        "feria_flores": {"month": 8, "days": [1, 10]}
                    }
                }
            }
        }
        with open(self.config_path, "w", encoding='utf-8') as f:
            yaml.dump(self.config_dict, f)

        self.analyzer = DataAnalyzer(config_path=self.config_path)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _generate_mock_data(self, n_days=50, stationary=True, seed=42):
        np.random.seed(seed)
        dates = pd.date_range(start="2023-01-01", periods=n_days)
        if stationary:
            # Ruido blanco puro es lo más seguro para que ADF detecte estacionariedad
            values = np.random.normal(100, 5, n_days)
        else:
            # Tendencia lineal clara asegura no estacionariedad
            values = np.linspace(0, 100, n_days) + np.random.normal(0, 2, n_days)
            
        df = pd.DataFrame({
            "target": values,
            "exog1": np.random.normal(50, 5, n_days),
            "exog2": np.random.normal(30, 3, n_days),
            "es_promocion": [0] * n_days,
            "precipitacion_mm": [0.0] * n_days,
            "temperatura_media": [20.0] * n_days,
            "smlv": [1000000] * n_days,
            "periodo": ["Post-Pandemia"] * n_days
        }, index=dates)
        df.index.name = "fecha"
        return df

    # --- FLUJOS POSITIVOS ---

    def test_split_data_correctness(self):
        """Verifica que la partición temporal respete los días definidos."""
        df = self._generate_mock_data(n_days=40)
        train, val, test = self.analyzer._split_data(df)
        
        self.assertEqual(len(test), 10)
        self.assertEqual(len(val), 10)
        self.assertEqual(len(train), 20)

    def test_analyze_stationarity_detection(self):
        """Verifica detección de estacionariedad."""
        # Serie Estacionaria
        df_stat = self._generate_mock_data(n_days=100, stationary=True)
        res_stat = self.analyzer._analyze_stationarity(df_stat["target"])
        self.assertTrue(res_stat["is_stationary"])
        
        # Serie No Estacionaria
        df_non_stat = self._generate_mock_data(n_days=100, stationary=False)
        res_non_stat = self.analyzer._analyze_stationarity(df_non_stat["target"])
        self.assertFalse(res_non_stat["is_stationary"])

    def test_analyze_anomalies_detection(self):
        """Verifica que detecte un spike inyectado manualmente."""
        df = self._generate_mock_data(n_days=40)
        # Inyectar anomalía gigante
        df.loc[df.index[20], "target"] += 500 
        
        from statsmodels.tsa.seasonal import seasonal_decompose
        decomp = seasonal_decompose(df["target"], period=7)
        
        res = self.analyzer._analyze_anomalies(df, decomp.resid)
        self.assertGreaterEqual(res["summary"]["total_outliers"], 1)
        self.assertIn(df.index[20].strftime('%Y-%m-%d'), res["unexplained_dates"])

    def test_full_run_positive(self):
        """Verifica que el método run complete con datos válidos."""
        df = self._generate_mock_data(n_days=100)
        df.to_parquet(os.path.join(self.data_dir, "master_data.parquet"))
        
        report = self.analyzer.run()
        self.assertEqual(report["phase"], "03_eda")
        self.assertIn("advanced_analytics", report)

    # --- FLUJOS NO POSITIVOS (Abogado del Diablo) ---

    def test_empty_dataframe_error(self):
        """Verifica comportamiento ante un DataFrame vacío."""
        df_empty = pd.DataFrame()
        with self.assertRaises(Exception):
            self.analyzer._split_data(df_empty)

    def test_missing_target_column(self):
        """Verifica que falle si no existe la columna objetivo."""
        df = self._generate_mock_data(n_days=30)
        df_missing = df.drop(columns=["target"])
        with self.assertRaises(KeyError):
            self.analyzer._analyze_decomposition(df_missing["target"])

    def test_insufficient_data_for_decomposition(self):
        """Verifica manejo de error cuando hay menos de 2 periodos."""
        df_short = self._generate_mock_data(n_days=10)
        res = self.analyzer._analyze_decomposition(df_short["target"])
        self.assertIn("error", res)

    def test_constant_data_variance(self):
        """Verifica que no explote con datos constantes."""
        df = self._generate_mock_data(n_days=50)
        df["target"] = 100
        df["exog1"] = 50
        res = self.analyzer._analyze_multicollinearity(df)
        self.assertIn("correlation", res)
        self.assertTrue(isinstance(res["vif_scores"], dict))

    def test_all_nans_series(self):
        """Verifica que maneje una serie llena de NaNs."""
        series_nan = pd.Series([np.nan] * 50)
        with self.assertRaises(Exception):
            self.analyzer._analyze_stationarity(series_nan)

    def test_excessive_split_config(self):
        """Verifica comportamiento cuando los splits superan la data total."""
        self.analyzer.config["eda"]["splits"]["test_days"] = 100
        df = self._generate_mock_data(n_days=50)
        train, val, test = self.analyzer._split_data(df)
        # test se lleva todo, train y val quedan vacíos
        self.assertEqual(len(train), 0)
        self.assertEqual(len(val), 0)
        self.assertEqual(len(test), 50)

if __name__ == '__main__':
    unittest.main()
