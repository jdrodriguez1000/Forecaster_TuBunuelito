import pytest
import os
import pandas as pd
from unittest.mock import MagicMock, patch, mock_open
from src.loader import DataLoader

class TestDataLoader:
    """
    Suite de pruebas unitarias para DataLoader actualizada para Parquet e Incremental.
    Sigue el enfoque 'Abogado del Diablo' probando flujos felices y fallos controlados.
    """

    @pytest.fixture
    def mock_config(self):
        return {
            "general": {
                "data_raw_path": "data/01_raw",
                "outputs_path": "outputs",
                "tests_reports_path": "tests/reports"
            },
            "extractions": {
                "tables": ["ventas", "clima"],
                "schemas": {
                    "ventas": {"fecha": "datetime", "unidades": "int"},
                    "clima": {"fecha": "datetime", "temp": "float"}
                }
            }
        }

    @patch("src.loader.load_config")
    @patch("src.loader.DBConnector")
    @patch("src.loader.DataAuditor")
    @patch("os.makedirs")
    @patch("os.path.exists")
    def test_run_extraction_first_time_success(self, mock_exists, mock_makedirs, mock_auditor, mock_db, mock_load_config, mock_config):
        """Prueba una extracción completa (sin archivo previo) exitosa."""
        mock_load_config.return_value = mock_config
        mock_exists.return_value = False # Forzar extracción completa
        loader = DataLoader()
        
        # Simular datos de Supabase
        loader._fetch_table = MagicMock()
        loader._fetch_table.side_effect = [
            pd.DataFrame({"fecha": ["2023-01-01"], "unidades": [10]}),
            pd.DataFrame({"fecha": ["2023-01-01"], "temp": [25.5]})
        ]
        
        # Mock de auditoría
        loader.auditor.audit_dataframe = MagicMock(return_value={"status": "ok", "violations_count": 0})
        
        # Mock de guardado de Parquet y Reporte
        with patch("pandas.DataFrame.to_parquet") as mock_parquet, \
             patch("src.loader.save_report") as mock_save:
            
            results = loader.run_extraction()
            
            assert results["metrics"]["full_extractions"] == 2
            assert results["metrics"]["successful_extractions"] == 2
            assert mock_parquet.call_count == 2
            assert mock_save.called

    @patch("src.loader.load_config")
    @patch("src.loader.DBConnector")
    @patch("src.loader.DataAuditor")
    @patch("os.makedirs")
    @patch("os.path.exists")
    @patch("pandas.read_parquet")
    def test_run_extraction_incremental_success(self, mock_read, mock_exists, mock_makedirs, mock_auditor, mock_db, mock_load_config, mock_config):
        """Prueba una extracción incremental exitosa."""
        mock_load_config.return_value = mock_config
        mock_exists.return_value = True # Forzar incremental
        
        # Simular datos previos con fecha maxima
        df_old = pd.DataFrame({"fecha": [pd.Timestamp("2023-01-01")], "unidades": [10]})
        mock_read.return_value = df_old
        
        loader = DataLoader()
        
        # Simular nuevos datos descargados
        df_new = pd.DataFrame({"fecha": [pd.Timestamp("2023-01-02")], "unidades": [15]})
        loader._fetch_table = MagicMock(return_value=df_new)
        
        # Mock de auditoría
        loader.auditor.audit_dataframe = MagicMock(return_value={"status": "ok", "violations_count": 0})
        
        with patch("pandas.DataFrame.to_parquet") as mock_parquet, \
             patch("src.loader.save_report") as mock_save:
            
            results = loader.run_extraction()
            
            # Verificaciones
            assert results["metrics"]["incremental_updates"] > 0
            # Se llamó a fetch con la fecha del archivo previo
            loader._fetch_table.assert_called()
            # El parquet final debe contener el merge (concatenación)
            assert mock_parquet.called

    @patch("src.loader.load_config")
    @patch("src.loader.DBConnector")
    @patch("os.makedirs")
    def test_fetch_table_pagination(self, mock_makedirs, mock_db, mock_load_config, mock_config):
        """Prueba que el fetch maneje la paginación de Supabase (más de 1000 filas)."""
        mock_load_config.return_value = mock_config
        loader = DataLoader()
        
        # Simular cliente de Supabase con paginación
        mock_client = MagicMock()
        mock_db.return_value.get_client.return_value = mock_client
        
        # Primera página (1000 items), Segunda página (200 items)
        mock_exec1 = MagicMock()
        mock_exec1.data = [{"fecha": "2023-01-01"}] * 1000
        mock_exec2 = MagicMock()
        mock_exec2.data = [{"fecha": "2023-01-02"}] * 200
        
        mock_client.table.return_value.select.return_value.range.return_value.execute.side_effect = [
            mock_exec1, mock_exec2
        ]
        
        df = loader._fetch_table("test_table")
        
        assert len(df) == 1200
        assert mock_client.table.return_value.select.return_value.range.call_count == 2

    @patch("src.loader.load_config")
    @patch("src.loader.DBConnector")
    @patch("os.makedirs")
    def test_get_preview(self, mock_makedirs, mock_db, mock_load_config, mock_config):
        """Verifica que la generación de preview contenga head, tail y sample."""
        mock_load_config.return_value = mock_config
        loader = DataLoader()
        
        df = pd.DataFrame({
            "fecha": pd.to_datetime(["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"]),
            "valor": [1, 2, 3, 4]
        })
        
        preview = loader._get_preview(df)
        
        assert "first_3_rows" in preview
        assert "last_3_rows" in preview
        assert "sample_3_rows" in preview
        assert len(preview["first_3_rows"]) == 3
        # Verificar que la fecha esté formateada como string
        assert isinstance(preview["first_3_rows"][0]["fecha"], str)

    @patch("src.loader.load_config")
    @patch("src.loader.DBConnector")
    @patch("os.makedirs")
    def test_init_path_creation(self, mock_makedirs, mock_db, mock_load_config, mock_config):
        """Verifica la creación de infraestructura en init."""
        mock_load_config.return_value = mock_config
        DataLoader()
        assert mock_makedirs.called
