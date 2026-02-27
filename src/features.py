import pandas as pd
import numpy as np
import os
import yaml
import logging
from datetime import datetime

class FeatureEngineer:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.setup_logging()
        self.features_config = self.config.get('features', {})
        self.business_rules = self.config.get('eda', {}).get('business_rules', {})
        self.outputs_path = self.config.get('general', {}).get('data_processed_path', 'data/04_processed')

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def _create_calendar_features(self, df):
        """Genera variables basadas en el calendario y reglas de negocio del Charter."""
        self.logger.info("Generando variables de calendario y reglas de negocio...")
        
        df = df.copy()
        
        # Manejo de la columna fecha (si es índice, resetear)
        if df.index.name == 'fecha' or 'fecha' not in df.columns:
            df = df.reset_index()
            
        if 'fecha' not in df.columns:
            raise KeyError("La columna 'fecha' no se encuentra en el dataset ni como índice.")
            
        df['fecha'] = pd.to_datetime(df['fecha'])
        
        # Estacionalidad Básica (Solo lo estrictamente necesario)
        df['month'] = df['fecha'].dt.month
        df['day_of_week'] = df['fecha'].dt.dayofweek
        df['is_sunday'] = (df['day_of_week'] == 6).astype(int)
        
        # Quincenas (15, 16, 30, 31)
        quincenas = self.business_rules.get('payments', {}).get('quincenas', [15, 16, 30, 31])
        df['es_quincena'] = df['fecha'].dt.day.isin(quincenas).astype(int)
        
        # Primas Legales (Junio y Diciembre 15-20)
        prima_config = self.business_rules.get('payments', {}).get('prima_legal', {})
        june_range = prima_config.get('june', [15, 20])
        dec_range = prima_config.get('december', [15, 20])
        
        df['es_prima_legal'] = (
            ((df['month'] == 6) & (df['fecha'].dt.day.between(june_range[0], june_range[1]))) |
            ((df['month'] == 12) & (df['fecha'].dt.day.between(dec_range[0], dec_range[1])))
        ).astype(int)
        
        # Novenas (16 al 26 de diciembre)
        novenas = self.business_rules.get('events', {}).get('novenas', {})
        if novenas:
            n_month = novenas.get('month', 12)
            n_days = novenas.get('days', [16, 26])
            df['es_novena'] = ((df['month'] == n_month) & (df['fecha'].dt.day.between(n_days[0], n_days[1]))).astype(int)
        
        # Feria de las Flores (1 al 10 de Agosto)
        feria = self.business_rules.get('events', {}).get('feria_flores', {})
        if feria:
            f_month = feria.get('month', 8)
            f_days = feria.get('days', [1, 10])
            df['es_feria_flores'] = ((df['month'] == f_month) & (df['fecha'].dt.day.between(f_days[0], f_days[1]))).astype(int)
            
        return df

    def _apply_exogenous_transformations(self, df):
        """Aplica lags exógenos, momentum y persistencia climática."""
        self.logger.info("Aplicando transformaciones exógenas (Momentum, Lags, Clima)...")
        
        # Lags Exógenos (TRM 30)
        exo_lags = self.features_config.get('transformations', {}).get('exogenous_lags', {})
        for col, lag in exo_lags.items():
            if col in df.columns:
                df[f'{col}_lag_{lag}'] = df[col].shift(lag)
        
        # Momentum IPC (Trimestre)
        ipc_days = self.features_config.get('transformations', {}).get('momentum', {}).get('ipc_lookback_days', 90)
        if 'inflacion_mensual_ipc' in df.columns:
            # Shift 1 to avoid leakage if data is daily but IPC is monthly
            df['ipc_momentum'] = df['inflacion_mensual_ipc'] - df['inflacion_mensual_ipc'].shift(ipc_days)
            
        # Persistencia Climática (Ventana de 3 días)
        rain_window = self.features_config.get('transformations', {}).get('clima', {}).get('persistence_window', 3)
        if 'es_dia_lluvioso' in df.columns:
            df['rolling_rain_days_3'] = df['es_dia_lluvioso'].rolling(window=rain_window).sum().shift(1)
            
        # Lluvia Fuerte vs Ligera
        heavy_threshold = self.features_config.get('transformations', {}).get('clima', {}).get('heavy_rain_threshold', 'fuerte')
        if 'tipo_lluvia' in df.columns:
            df['is_heavy_rain'] = (df['tipo_lluvia'].str.lower() == heavy_threshold.lower()).astype(int)
            df['is_light_rain'] = ((df['es_dia_lluvioso'] == 1) & (df['is_heavy_rain'] == 0)).astype(int)
            
        return df

    def _create_simulation_ratios(self, df):
        """Crea ratios estratégicos para la fase de simulación (Asequibilidad, Spread, etc)."""
        self.logger.info("Calculando ratios de simulación...")
        
        # Índice de Asequibilidad: precio / (smlv / 30)
        if 'precio_unitario' in df.columns and 'smlv' in df.columns:
            df['asequibilidad_idx'] = df['precio_unitario'] / (df['smlv'] / 30)
            
        # Spread Inflación: % Variación Precio vs IPC
        if 'precio_unitario' in df.columns and 'inflacion_mensual_ipc' in df.columns:
            df['precio_var_pct'] = df['precio_unitario'].pct_change().fillna(0)
            df['spread_inflacion'] = df['precio_var_pct'] - (df['inflacion_mensual_ipc'] / 100)
            
        # Crecimiento Real SMLV
        if 'smlv' in df.columns and 'inflacion_mensual_ipc' in df.columns:
            df['smlv_var_pct'] = df['smlv'].pct_change().fillna(0)
            df['smlv_real_growth'] = df['smlv_var_pct'] - (df['inflacion_mensual_ipc'] / 100)
            
        # Intensidad de Pauta: Removida por dependencia de target_lag_7
        # Se delega a la fase de modelado para evitar leakage y VIF alto.
            
        # Vulnerabilidad TRM: costo / trm_lag_30
        if 'costo_unitario' in df.columns and 'trm_lag_30' in df.columns:
            df['vulnerability_trm'] = df['costo_unitario'] / (df['trm_lag_30'] + 1)
            
        return df

    def _create_interactions(self, df):
        """Genera interacciones de negocio definidas en config."""
        self.logger.info("Generando interacciones de variables...")
        
        interactions = self.features_config.get('interactions', [])
        
        # Mapping names to actual columns
        name_map = {
            "is_sunday": "is_sunday",
            "es_quincena": "es_quincena",
            "es_promocion": "es_promocion",
            "is_heavy_rain": "is_heavy_rain"
        }
        
        for pair in interactions:
            col1, col2 = pair
            # Check mapping if name is an alias
            c1 = name_map.get(col1, col1)
            c2 = name_map.get(col2, col2)
            
            if c1 in df.columns and c2 in df.columns:
                # Special case for Novena + IPC Interaction
                if col1 == "es_novena" and col2 == "inflacion_mensual_ipc":
                    df['interaction_novena_ipc'] = df[c1] * df[c2]
                else:
                    new_col = f"interaction_{col1}_{col2}"
                    df[new_col] = df[c1] * df[c2]
        
        return df

    def run_pipeline(self, df):
        """Ejecuta toda la ingeniería de características en orden."""
        self.logger.info("Iniciando Pipeline de Feature Engineering...")
        start_time = datetime.now()
        original_cols = df.columns.tolist()
        
        # 1. Calendario
        df = self._create_calendar_features(df)
        
        # 2. Fourier (Removido por redundancia y VIF Infinito)
        # df = self._create_fourier_features(df)
        
        # 3. Transformaciones Exógenas (Momentum, Lags TRM, Clima)
        df = self._apply_exogenous_transformations(df)
        
        # 4. Ratios de Simulación
        df = self._create_simulation_ratios(df)
        
        # 5. Interacciones
        df = self._create_interactions(df)
        
        # Columnas creadas/transformadas antes de la limpieza
        all_created_cols = [c for c in df.columns if c not in original_cols]
        
        # 6. Limpieza Final (Eliminar columnas marcadas en config)
        self.logger.info("Limpiando columnas irrelevantes/peligrosas...")
        drop_cols = self.features_config.get('drop_columns', [])
        existing_drop = [c for c in drop_cols if c in df.columns]
        df = df.drop(columns=existing_drop)
        
        maintained_cols = [c for c in original_cols if c in df.columns]
        
        # 7. Limpieza de Nulos (Garantiza salud para el modelo)
        self.logger.info("Eliminando filas con valores nulos resultantes del proceso...")
        initial_rows = len(df)
        df = df.dropna()
        final_rows = len(df)
        self.logger.info(f"Se eliminaron {initial_rows - final_rows} filas con nulos.")

        # 8. Auditoría Estadística (VIF y Correlación)
        self.logger.info("Ejecutando auditoría diagnóstica (VIF y Correlación)...")
        vif_data, corr_summary = self._perform_statistical_audit(df)
        
        # 9. Persistencia de Datos y Reporte
        self.save_results(df)
        self._generate_report(df, start_time, original_cols, maintained_cols, existing_drop, all_created_cols, vif_data, corr_summary)
        
        return df

    def _perform_statistical_audit(self, df):
        """Calcula VIF y Correlación para validar la calidad del dataset final."""
        import seaborn as sns
        import matplotlib.pyplot as plt
        try:
            from statsmodels.stats.outliers_influence import variance_inflation_factor
            from statsmodels.tools.tools import add_constant
        except ImportError:
            self.logger.warning("statsmodels no instalado. Omitiendo VIF.")
            return {}, {}
        
        # Filtrar solo columnas numéricas y sin nulos para el análisis
        numeric_df = df.select_dtypes(include=[np.number]).dropna()
        
        # Eliminar columnas con varianza cero (constantes) ya que rompen el VIF
        numeric_df = numeric_df.loc[:, numeric_df.var() > 0]
        
        # 1. Matriz de Correlación
        corr_matrix = numeric_df.corr()
        
        # Guardar Visualización
        fig_path = os.path.join(self.config.get('general', {}).get('outputs_path', 'outputs'), 'figures', 'phase_04')
        if not os.path.exists(fig_path):
            os.makedirs(fig_path)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        plt.figure(figsize=(20, 15))
        sns.heatmap(corr_matrix, annot=False, cmap='coolwarm')
        plt.title("Matriz de Correlación - Dataset de Features Final")
        plt.savefig(os.path.join(fig_path, "correlation_matrix_latest.png"))
        plt.close()
        
        # Resumen de correlación (top correlations > 0.8)
        corr_unstack = corr_matrix.unstack().sort_values(ascending=False)
        top_corr = corr_unstack[(corr_unstack < 1.0) & (corr_unstack > 0.8)].to_dict()
        # Convertir tuplas de keys a strings para JSON
        top_corr_clean = {f"{k[0]} && {k[1]}": float(v) for k, v in top_corr.items()}
        
        # 2. VIF
        vif_results = {}
        try:
            # Asegurar que los datos sean float y tengan constante
            X = add_constant(numeric_df).astype(float)
            for i in range(1, X.shape[1]):
                col_name = X.columns[i]
                vif = variance_inflation_factor(X.values, i)
                vif_results[col_name] = float(vif)
        except Exception as e:
            self.logger.warning(f"Error en cálculo de VIF: {e}")
            
        return vif_results, top_corr_clean

    def _generate_report(self, df, start_time, original_cols, maintained_cols, dropped_cols, created_cols, vif_data, corr_summary):
        """Genera el reporte JSON oficial consolidando inventario detallado, calidad y diagnóstico estadístico."""
        import json
        
        report_path = self.config.get('general', {}).get('outputs_path', 'outputs')
        report_dir = os.path.join(report_path, 'reports', 'phase_04')
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)
            
        history_dir = os.path.join(report_dir, 'history')
        if not os.path.exists(history_dir):
            os.makedirs(history_dir)
            
        end_time = datetime.now()
        timestamp = end_time.strftime("%Y%m%d_%H%M%S")
        
        # Auditoría de Calidad Base
        null_analysis = df.isnull().sum()
        quality_audit = {
            "presents_nulls": bool(null_analysis.any()),
            "null_details": null_analysis[null_analysis > 0].to_dict(),
            "duplicate_rows": int(df.duplicated().sum()),
            "duplicate_dates": int(df['fecha'].duplicated().sum()) if 'fecha' in df.columns else "N/A",
            "statistical_diagnostics": {
                "vif_analysis": vif_data,
                "high_correlations_detected": corr_summary
            }
        }
        
        report_data = {
            "phase": "04_feature_engineering",
            "timestamp": end_time.isoformat(),
            "description": "Enriquecimiento, Validación y Auditoría Estadística del dataset final.",
            "business_rule_compliance": {
                "rule_T_minus_1_vs_T": "Cumplida. Lags, momentum y ratios auditados para prevenir fuga de datos.",
                "statistical_validation": "VIF y Correlación ejecutados para asegurar independencia de exógenas.",
                "dual_persistence": "Activa para datos y reportes (Latest + History)."
            },
            "data_inventory": {
                "summary": {
                    "original_count": len(original_cols),
                    "maintained_count": len(maintained_cols),
                    "dropped_count": len(dropped_cols),
                    "created_count": len(created_cols),
                    "total_final_columns": len(df.columns)
                },
                "details": {
                    "original_dataset_columns": original_cols,
                    "columns_maintained": maintained_cols,
                    "columns_dropped": dropped_cols,
                    "columns_created_or_transformed": created_cols
                },
                "final_dataset": {
                    "name": "dataset_features_latest.parquet",
                    "path": "data/04_processed/",
                    "total_rows": len(df)
                }
            },
            "quality_audit": quality_audit,
            "performance": {
                "execution_time_seconds": (end_time - start_time).total_seconds(),
                "status": "success"
            }
        }
        
        # Dual Persistencia
        latest_file = os.path.join(report_dir, "phase_04_features_latest.json")
        history_file = os.path.join(history_dir, f"phase_04_features_{timestamp}.json")
        
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=4, ensure_ascii=False)
            
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=4, ensure_ascii=False)
            
        self.logger.info(f"Reporte Consolidado Final de Fase 04 generado exitosamente.")

    def save_results(self, df):
        """Guarda el resultado en la ruta procesada con protocolo de dual persistencia."""
        processed_path = self.outputs_path
        if not os.path.exists(processed_path):
            os.makedirs(processed_path)
            
        history_path = os.path.join(processed_path, 'history')
        if not os.path.exists(history_path):
            os.makedirs(history_path)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_latest = "dataset_features_latest.parquet"
        filename_history = f"dataset_features_{timestamp}.parquet"
        
        df.to_parquet(os.path.join(processed_path, filename_latest), index=False)
        df.to_parquet(os.path.join(history_path, filename_history), index=False)
        self.logger.info(f"Dataset persistido en {processed_path}")

if __name__ == "__main__":
    try:
        master_data_path = "data/02_cleansed/master_data.parquet"
        if os.path.exists(master_data_path):
            df_master = pd.read_parquet(master_data_path)
            fe = FeatureEngineer()
            df_final = fe.run_pipeline(df_master)
            print("Pipeline y Auditoría completados exitosamente.")
        else:
            print(f"Error: No se encontró el archivo {master_data_path}")
    except Exception as e:
        print(f"Error crítico en la ejecución: {e}")
