import unittest
import pandas as pd
import numpy as np
import os
import shutil
from src.preprocessor import DataPreprocessor

class TestDataPreprocessor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Crear un config temporal para las pruebas
        cls.test_dir = os.path.abspath("tests/temp_preprocessor")
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)
        os.makedirs(cls.test_dir, exist_ok=True)
        os.makedirs(os.path.join(cls.test_dir, "raw"), exist_ok=True)
        os.makedirs(os.path.join(cls.test_dir, "cleansed"), exist_ok=True)
        os.makedirs(os.path.join(cls.test_dir, "outputs/reports/phase_02"), exist_ok=True)
        
        # Mock de configuración mínima necesaria
        cls.config_path = os.path.join(cls.test_dir, "test_config.yaml")
        try:
            with open(cls.config_path, "w", encoding='utf-8') as f:
                f.write(f"""
general:
  data_raw_path: "{cls.test_dir.replace('\\', '/')}/raw"
  data_cleansed_path: "{cls.test_dir.replace('\\', '/')}/cleansed"
  outputs_path: "{cls.test_dir.replace('\\', '/')}/outputs"
extractions:
  tables: ["ventas", "inventario", "clima", "finanzas", "marketing", "macroeconomia"]
  schemas:
    ventas:
      fecha: "date"
      unidades_totales: "int"
      unidades_pagas: "int"
      unidades_bonificadas: "int"
      es_promocion: "int"
    inventario:
      fecha: "date"
      ventas_reales_pagas: "int"
      ventas_reales_bonificadas: "int"
      buñuelos_preparados: "int"
      ventas_reales_totales: "int"
      buñuelos_desperdiciados: "int"
      unidades_agotadas: "int"
      demanda_teorica_total: "int"
    clima:
      fecha: "date"
      temperatura_media: "float"
      tipo_lluvia: "str"
      es_dia_lluvioso: "int"
    finanzas:
      fecha: "date"
      precio_unitario: "int"
      costo_unitario: "float"
      margen_bruto: "float"
      porcentaje_margen: "float"
    marketing:
      fecha: "date"
      ig_cost: "int"
      fb_cost: "int"
      inversion_total: "int"
      ig_pct: "float"
      fb_pct: "float"
      campaña_activa: "int"
    macroeconomia:
      fecha: "date"
      smlv: "int"
  sentinel_values:
    nulls: [-999, "NULL", "N/A"]
                """)
            
            cls.preprocessor = DataPreprocessor(config_path=cls.config_path)
        except Exception as e:
            print(f"ERROR EN SETUP: {str(e)}")
            raise e

    @classmethod
    def tearDownClass(cls):
        # Limpiar archivos temporales
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)

    def test_clean_ventas_promotions(self):
        """Prueba la corrección de unidades bonificadas en promoción."""
        data = {
            "fecha": ["2023-01-01", "2023-01-02"],
            "unidades_pagas": [10, 10],
            "unidades_bonificadas": [5, 5], # En promo debería ser 10
            "es_promocion": [1, 0],
            "unidades_totales": [15, 15]
        }
        df = pd.DataFrame(data)
        df_clean, audit = self.preprocessor._clean_table(df, "ventas")
        
        # El primer registro (promo) debe tener 10 bonificadas
        self.assertEqual(df_clean.iloc[0]["unidades_bonificadas"], 10)
        self.assertEqual(df_clean.iloc[0]["unidades_totales"], 20)
        # El segundo (no promo) se mantiene igual
        self.assertEqual(df_clean.iloc[1]["unidades_bonificadas"], 5)
        self.assertEqual(audit["ajustes_bonificadas_promocion"], 1)

    def test_clean_inventario_demand(self):
        """Prueba el recálculo de la verdad absoluta de demanda."""
        data = {
            "fecha": ["2023-01-01"],
            "ventas_reales_pagas": [100],
            "ventas_reales_bonificadas": [50],
            "buñuelos_preparados": [200],
            "unidades_agotadas": [10],
            "demanda_teorica_total": [120] # Inconsistente (debería ser 150 + 10 = 160)
        }
        df = pd.DataFrame(data)
        df_clean, audit = self.preprocessor._clean_table(df, "inventario")
        
        # Demanda = (100+50) + 10 = 160
        self.assertEqual(df_clean.iloc[0]["demanda_teorica_total"], 160)
        self.assertEqual(df_clean.iloc[0]["buñuelos_desperdiciados"], 50) # 200 - 150
        self.assertEqual(audit["correccion_demanda_inconsistente"], 1)

    def test_imputation_clima(self):
        """Prueba imputaciones de clima y columna es_dia_lluvioso."""
        data = {
            "fecha": ["2023-01-01", "2023-01-02", "2023-01-03"],
            "temperatura_media": [20.0, np.nan, 22.0],
            "tipo_lluvia": ["Fuerte", np.nan, "Ninguna"],
            "es_dia_lluvioso": [1, np.nan, 0]
        }
        df = pd.DataFrame(data)
        # Seteamos el tipo_lluvia para que la moda sea 'Fuerte' o 'Ninguna'
        # En este caso, el preprocesador imputará la moda o 'Ninguna' por defecto.
        df_clean, audit = self.preprocessor._clean_table(df, "clima")
        
        self.assertFalse(df_clean["temperatura_media"].isnull().any())
        self.assertEqual(df_clean.iloc[1]["temperatura_media"], 20.0) # ffill
        
        # Si tipo_lluvia es imputado (ej. 'Ninguna' por moda), es_dia_lluvioso debe ser 0
        tipo_imputado = df_clean.iloc[1]["tipo_lluvia"]
        expected_val = 0 if tipo_imputado == "Ninguna" else 1
        self.assertEqual(df_clean.iloc[1]["es_dia_lluvioso"], expected_val)

    def test_imputation_finanzas(self):
        """Prueba imputación de precios y recálculo de márgenes."""
        data = {
            "fecha": ["2023-01-01", "2023-01-02"],
            "precio_unitario": [1000, np.nan],
            "costo_unitario": [500, np.nan],
            "margen_bruto": [500, np.nan],
            "porcentaje_margen": [0.5, np.nan]
        }
        df = pd.DataFrame(data)
        df_clean, audit = self.preprocessor._clean_table(df, "finanzas")
        
        self.assertEqual(df_clean.iloc[1]["precio_unitario"], 1000)
        self.assertEqual(df_clean.iloc[1]["margen_bruto"], 500)
        self.assertEqual(df_clean.iloc[1]["porcentaje_margen"], 0.5)

    def test_imputation_marketing(self):
        """Prueba lógica de inversión y campaña activa."""
        data = {
            "fecha": ["2023-01-01", "2023-01-02"],
            "ig_cost": [100, 0],
            "fb_cost": [0, 0],
            "campaña_activa": [0, 1] # Valores incorrectos a resetear
        }
        df = pd.DataFrame(data)
        df_clean, audit = self.preprocessor._clean_table(df, "marketing")
        
        self.assertEqual(df_clean.iloc[0]["campaña_activa"], 1) # ig_cost > 0
        self.assertEqual(df_clean.iloc[1]["campaña_activa"], 0) # ambos 0
        self.assertEqual(df_clean.iloc[0]["inversion_total"], 100)
        self.assertEqual(df_clean.iloc[0]["ig_pct"], 1.0)

    def test_merge_master_integrity(self):
        """Prueba que el merge maestro reporte correctamente y maneje el índice."""
        # Necesitamos archivos reales para _merge_master ya que lee de disco
        os.makedirs(os.path.join(self.test_dir, "cleansed"), exist_ok=True)
        
        df1 = pd.DataFrame({"fecha": pd.to_datetime(["2023-01-01"]), "val1": [1]})
        df2 = pd.DataFrame({"fecha": pd.to_datetime(["2023-01-01"]), "val2": [2]})
        
        df1.to_parquet(os.path.join(self.test_dir, "cleansed/ventas.parquet"), index=False)
        df2.to_parquet(os.path.join(self.test_dir, "cleansed/inventario.parquet"), index=False)
        
        reports = {
            "ventas": {"status": "success"},
            "inventario": {"status": "success"}
        }
        
        audit = self.preprocessor._merge_master(reports)
        
        self.assertEqual(audit["total_rows"], 1)
        self.assertEqual(audit["index_name"], "fecha")
        self.assertEqual(audit["null_values_count"], 0)

    # --- FLUJOS NO POSITIVOS (Abogado del Diablo) ---

    def test_clean_table_unknown_name(self):
        """Verifica que el preprocesador maneje tablas desconocidas devolviendo el DF original."""
        df = pd.DataFrame({"col1": [1, 2]})
        df_clean, audit = self.preprocessor._clean_table(df, "tabla_fantasma")
        pd.testing.assert_frame_equal(df, df_clean)
        self.assertEqual(audit["status"], "success")
        self.assertIn("warning", audit)

    def test_clean_table_missing_columns(self):
        """Verifica que el recalculo de demanda no explote si faltan columnas críticas."""
        # Si falta 'unidades_agotadas', el cálculo fallará
        data = {"fecha": ["2023-01-01"], "ventas_reales_pagas": [100]}
        df = pd.DataFrame(data)
        # Debería capturar el error y poner status='error' en el reporte
        df_clean, audit = self.preprocessor._clean_table(df, "inventario")
        self.assertEqual(audit["status"], "error")
        self.assertIn("error", audit)

    def test_sentinel_values_conversion(self):
        """Prueba que los valores centinela (-999, 'NULL') se conviertan a NaN."""
        data = {
            "fecha": ["2023-01-01", "2023-01-02", "2023-01-03"],
            "unidades_pagas": [10, -999, 12],
            "es_promocion": [0, "NULL", 1]
        }
        df = pd.DataFrame(data)
        # Usamos 'ventas' porque no tiene ffill/bfill automático en estas columnas
        df_clean, audit = self.preprocessor._clean_table(df, "ventas")
        
        self.assertTrue(pd.isna(df_clean.loc[1, "unidades_pagas"]))
        self.assertTrue(pd.isna(df_clean.loc[1, "es_promocion"]))

    def test_merge_master_missing_files(self):
        """Verifica que el merge maestro falle o reporte error si faltan archivos físicos."""
        reports = {"ventas": {"status": "success"}}
        # Eliminamos el archivo ventas.parquet si existe
        ventas_path = os.path.join(self.test_dir, "cleansed/ventas.parquet")
        if os.path.exists(ventas_path):
            os.remove(ventas_path)
            
        with self.assertRaises(Exception):
            self.preprocessor._merge_master(reports)

    def test_invalid_date_format_in_input(self):
        """Verifica manejo de fechas corruptas."""
        data = {"fecha": ["fecha_invalida", "2023-01-01"], "unidades_pagas": [10, 20]}
        df = pd.DataFrame(data)
        df_clean, audit = self.preprocessor._clean_table(df, "ventas")
        # El preprocessor ahora captura el error en el audit
        self.assertEqual(audit["status"], "error")
        self.assertIn("error", audit)

    def test_empty_input(self):
        """Verifica que no explote con un DF vacío."""
        df = pd.DataFrame()
        df_clean, audit = self.preprocessor._clean_table(df, "ventas")
        self.assertEqual(audit["status"], "error") # Porque faltan columnas obligatorias de ventas logic


if __name__ == '__main__':
    unittest.main()
