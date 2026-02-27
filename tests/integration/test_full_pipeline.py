import pytest
import subprocess
import os
import json
from src.utils.config_loader import load_config

class TestFullPipelineIntegration:
    """
    Prueba de Integración End-to-End (E2E) para el Pipeline.
    Ejecuta main.py y valida la transición completa de datos.
    """

    @classmethod
    def setup_class(cls):
        cls.config = load_config()
        cls.outputs_path = cls.config.get("general", {}).get("outputs_path")
        cls.reports_path = os.path.join(cls.outputs_path, "reports")

    def test_pipeline_train_mode_execution(self):
        """
        [E2E] Ejecuta 'python main.py --mode train' y valida la cascada de fases.
        """
        # 1. Ejecutar el comando
        result = subprocess.run(
            ["python", "main.py", "--mode", "train"],
            capture_output=True,
            text=True
        )

        # 2. Validar que terminó sin errores
        combined_output = result.stdout + result.stderr
        assert result.returncode == 0, f"Error en ejecución de main.py: {result.stderr}"
        
        # 3. Validar logs de las fases en la salida combinada
        assert "Fase 01 completada exitosamente" in combined_output
        assert "Fase 02 completada exitosamente" in combined_output
        assert "Fase 03 completada exitosamente" in combined_output

        # 4. Validar existencia física de reportes (punteros 'latest')
        assert os.path.exists(os.path.join(self.reports_path, "phase_01", "phase_01_extractions_latest.json"))
        assert os.path.exists(os.path.join(self.reports_path, "phase_02", "phase_02_preprocessing_latest.json"))
        assert os.path.exists(os.path.join(self.reports_path, "phase_03", "phase_03_eda_latest.json"))

    def test_pipeline_load_mode_execution(self):
        """
        [E2E] Ejecuta 'python main.py --mode load' y valida que solo corra la extracción.
        """
        result = subprocess.run(
            ["python", "main.py", "--mode", "load"],
            capture_output=True,
            text=True
        )

        combined_output = result.stdout + result.stderr
        assert result.returncode == 0
        assert "Fase 01 completada exitosamente" in combined_output
        # En modo load, NO debería correr Preprocesamiento ni EDA
        assert "Fase 02 completada exitosamente" not in combined_output
        assert "Fase 03 completada exitosamente" not in combined_output
