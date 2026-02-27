import pytest
import os
import pandas as pd
import json
from src.analyzer import DataAnalyzer
from src.utils.config_loader import load_config

class TestEDAIntegration:
    """
    Pruebas de Integración para el flujo de Análisis Exploratorio (Fase 03).
    Valida la generación de insights, reportes y figuras a partir del Master Data.
    """

    @classmethod
    def setup_class(cls):
        """Prepara el entorno para pruebas de integración."""
        cls.config = load_config()
        cls.cleansed_path = cls.config.get("general", {}).get("data_cleansed_path")
        cls.outputs_path = cls.config.get("general", {}).get("outputs_path")
        cls.reports_path = os.path.join(cls.outputs_path, "reports/phase_03")
        cls.figures_path = os.path.join(cls.outputs_path, "figures/phase_03")
        cls.analyzer = DataAnalyzer()

    def test_full_eda_flow(self):
        """
        [POSITIVO] Ejecuta el EDA completo y valida la existencia del reporte y las figuras.
        """
        # 1. Asegurar que exista el Master Data (Fase 02 previa)
        master_file = os.path.join(self.cleansed_path, "master_data.parquet")
        assert os.path.exists(master_file), "Falta master_data.parquet. Ejecuta la Fase 02 primero."

        # 2. Ejecutar EDA
        report = self.analyzer.run()

        # 3. Validar Estructura del Reporte
        assert report["phase"] == "03_eda"
        assert "statistical_audit" in report
        assert "business_insights" in report
        assert "advanced_analytics" in report
        
        # Validar métricas de split
        assert report["data_splits"]["train"] > 0
        assert "test" in report["data_splits"]

        # 4. Validar Persistencia del Reporte
        report_file = os.path.join(self.reports_path, "phase_03_eda_latest.json")
        assert os.path.exists(report_file)

        with open(report_file, "r", encoding="utf-8") as f:
            persisted_report = json.load(f)
        assert persisted_report["phase"] == "03_eda"

    def test_figures_generation(self):
        """
        [POSITIVO] Verifica que las gráficas críticas se hayan generado físicamente.
        """
        expected_figures = [
            "time_series_decomposition_latest.png",
            "acf_pacf_analysis_latest.png",
            "correlation_matrix_latest.png",
            "weekly_hierarchy_box_latest.png",
            "period_analysis_box_latest.png",
            "anomaly_detection_latest.png",
            "variance_stability_latest.png",
            "frequency_analysis_latest.png"
        ]

        for fig in expected_figures:
            fig_path = os.path.join(self.figures_path, fig)
            assert os.path.exists(fig_path), f"Falta la figura crítica: {fig}"

    def test_business_logic_consistency(self):
        """
        [LÓGICA] Valida que los insights de negocio tengan las llaves esperadas.
        """
        report_file = os.path.join(self.reports_path, "phase_03_eda_latest.json")
        with open(report_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        insights = data["business_insights"]
        
        # Verificar que se hayan evaluado las reglas de negocio base
        assert "01_weekly_hierarchy" in insights
        assert "02_holiday_impact" in insights
        assert "03_financial_cycles" in insights
        assert "04_special_events" in insights
        
        # Revisamos una métrica cualquiera del insight semanal
        sample_insight = insights["01_weekly_hierarchy"]
        assert "mean" in sample_insight
        assert "Monday" in sample_insight["mean"]
        assert len(sample_insight["mean"]) == 7 # 7 días de la semana
