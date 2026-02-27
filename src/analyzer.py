import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import logging
from datetime import datetime
import holidays
from statsmodels.tsa.stattools import adfuller, acf, pacf, ccf
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools.tools import add_constant
from scipy import signal

from src.utils.config_loader import load_config
from src.utils.helpers import save_report

class DataAnalyzer:
    """
    Clase encargada de la Fase 03: Análisis Exploratorio de Datos (EDA).
    Implementa rigor científico, descomposición de series, validación de hipótesis, 
    interacciones cruciales y análisis de retardos (Lead/Lag).
    """

    def __init__(self, config_path="config.yaml"):
        self.config = load_config(config_path)
        self.setup_logging()
        
        self.output_path = self.config.get("general", {}).get("outputs_path", "outputs")
        self.figures_path = os.path.join(self.output_path, "figures/phase_03")
        self.reports_path = os.path.join(self.output_path, "reports/phase_03")
        
        # Crear directorios si no existen
        os.makedirs(self.figures_path, exist_ok=True)
        os.makedirs(self.reports_path, exist_ok=True)
        os.makedirs(os.path.join(self.reports_path, "history"), exist_ok=True)
        os.makedirs(os.path.join(self.figures_path, "history"), exist_ok=True)

        self.target = self.config.get("eda", {}).get("target_variable", "demanda_teorica_total")
        self.random_state = self.config.get("general", {}).get("random_state", 42)
        
        # Instanciar festivos de Colombia
        self.co_holidays = holidays.CO()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _split_data(self, df):
        """Divide el dataset en Train, Validation y Test basándose en fechas."""
        self.logger.info("Ejecutando Triple Partición Temporal (Train/Val/Test)...")
        test_days = self.config.get("eda", {}).get("splits", {}).get("test_days", 185)
        val_days = self.config.get("eda", {}).get("splits", {}).get("val_days", 185)
        
        df = df.sort_index()
        test_split_date = df.index.max() - pd.Timedelta(days=test_days)
        val_split_date = test_split_date - pd.Timedelta(days=val_days)
        
        train_df = df[df.index <= val_split_date]
        val_df = df[(df.index > val_split_date) & (df.index <= test_split_date)]
        test_df = df[df.index > test_split_date]
        
        return train_df, val_df, test_df

    def _analyze_decomposition(self, series):
        """Descompone la serie en Tendencia, Estacionalidad y Residuo."""
        self.logger.info("Analizando Descomposición de Serie Temporal...")
        try:
            decomposition = seasonal_decompose(series.dropna(), model='additive', period=7)
            fig = decomposition.plot()
            fig.set_size_inches(12, 10)
            plt.tight_layout(rect=[0, 0.03, 1, 0.95])
            self._save_figure(fig, "time_series_decomposition")
            return {
                "trend_mean": float(decomposition.trend.mean()),
                "seasonal_strength": float(decomposition.seasonal.std()),
                "resid_mean": float(decomposition.resid.mean()),
                "resid_std": float(decomposition.resid.std())
            }
        except Exception as e:
            return {"error": str(e)}

    def _analyze_stationarity(self, series):
        """Prueba de Dickey-Fuller Aumentada (ADF)."""
        result = adfuller(series.dropna())
        return {
            "test_statistic": float(result[0]),
            "p_value": float(result[1]),
            "critical_values": {k: float(v) for k, v in result[4].items()},
            "is_stationary": bool(result[1] < 0.05)
        }

    def _analyze_autocorrelation(self, series):
        """Genera ACF y PACF con valores numéricos."""
        n_lags = self.config.get("eda", {}).get("time_series", {}).get("lags_acf_pacf", 40)
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        plot_acf(series.dropna(), lags=n_lags, ax=ax1)
        plot_pacf(series.dropna(), lags=n_lags, ax=ax2)
        plt.tight_layout()
        self._save_figure(fig, "acf_pacf_analysis")
        
        acf_vals, pacf_vals = acf(series.dropna(), nlags=n_lags), pacf(series.dropna(), nlags=n_lags)
        return {"lags_analyzed": n_lags, "values": {f"lag_{i}": {"acf": float(acf_vals[i]), "pacf": float(pacf_vals[i])} for i in range(len(acf_vals))}}

    def _analyze_multicollinearity(self, df):
        """Matriz de Correlación y VIF."""
        vif_cols = self.config.get("eda", {}).get("statistics", {}).get("vif_columns", [])
        available_cols = [c for c in vif_cols if c in df.columns]
        corr_matrix = df[available_cols + [self.target]].corr()
        
        fig, ax = plt.subplots(figsize=(12, 10))
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt=".2f", ax=ax)
        self._save_figure(fig, "correlation_matrix")
        
        vif_data = pd.DataFrame()
        X = df[available_cols].dropna()
        if not X.empty:
            X_const = add_constant(X)
            vif_data["feature"] = X_const.columns
            vif_data["vif"] = [variance_inflation_factor(X_const.values, i) for i in range(X_const.shape[1])]
            vif_data = vif_data[vif_data["feature"] != "const"]
        
        return {"correlation": corr_matrix.to_dict(), "vif_scores": vif_data.set_index("feature")["vif"].to_dict()}

    def _validate_hypotheses(self, df):
        """Validaciones de negocio detalladas."""
        self.logger.info("Validando Hipótesis de Negocio...")
        df = df.copy()
        df['day_name'] = df.index.day_name()
        df['month'] = df.index.month
        df['day'] = df.index.day
        df['year'] = df.index.year
        
        res = {}
        # H1: Weekly
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        res["01_weekly_hierarchy"] = df.groupby('day_name')[self.target].agg(['mean', 'median', 'count']).reindex(day_order).to_dict()
        self._plot_box(df, 'day_name', self.target, "Weekly Hierarchy", "weekly_hierarchy_box", order=day_order)

        # H2: Holidays
        df['es_festivo_co'] = df.index.map(lambda x: 1 if x in self.co_holidays else 0)
        res["02_holiday_impact"] = df.groupby('es_festivo_co')[self.target].agg(['mean', 'median', 'count']).to_dict()

        # H3: Payments
        df['is_quincena'] = df['day'].isin(self.config['eda']['business_rules']['payments']['quincenas']).astype(int)
        df['is_prima'] = (((df['month'] == 6) | (df['month'] == 12)) & (df['day'] >= 15) & (df['day'] <= 20)).astype(int)
        res["03_financial_cycles"] = {
            "quincena": df.groupby('is_quincena')[self.target].agg(['mean', 'median', 'count']).to_dict(),
            "prima": df.groupby('is_prima')[self.target].agg(['mean', 'median', 'count']).to_dict()
        }

        # H4: Events
        novenas = self.config['eda']['business_rules']['events']['novenas']
        df['is_novena'] = ((df['month'] == novenas['month']) & (df['day'] >= novenas['days'][0]) & (df['day'] <= novenas['days'][1])).astype(int)
        feria = self.config['eda']['business_rules']['events']['feria_flores']
        df['is_feria'] = ((df['month'] == feria['month']) & (df['day'] >= feria['days'][0]) & (df['day'] <= feria['days'][1])).astype(int)
        res["04_special_events"] = {
            "novenas": df.groupby('is_novena')[self.target].agg(['mean', 'median', 'count']).to_dict(),
            "feria": df.groupby('is_feria')[self.target].agg(['mean', 'median', 'count']).to_dict()
        }

        # H5: Promos
        if 'es_promocion' in df.columns:
            res["05_promotion_impact"] = df.groupby('es_promocion')[self.target].agg(['mean', 'median', 'count']).to_dict()
            self._plot_box(df, 'es_promocion', self.target, "Impact of Promotions", "promotion_impact_box")

        # H6: Weather
        if 'precipitacion_mm' in df.columns:
            df['clima_cat'] = 'Ninguna'
            df.loc[(df['precipitacion_mm'] > 0) & (df['precipitacion_mm'] <= 2), 'clima_cat'] = 'Ligera'
            df.loc[(df['precipitacion_mm'] > 2) & (df['precipitacion_mm'] <= 7), 'clima_cat'] = 'Moderada'
            df.loc[df['precipitacion_mm'] > 7, 'clima_cat'] = 'Fuerte'
            res["06_weather_impact"] = {
                "rain": df.groupby('clima_cat')[self.target].agg(['mean', 'median', 'count']).to_dict()
            }
        if 'temperatura_media' in df.columns:
            df['temp_cat'] = pd.cut(df['temperatura_media'], bins=[-np.inf, 18, 22, np.inf], labels=['Frío', 'Templado', 'Cálido'])
            res["06_weather_impact"]["temp"] = df.groupby('temp_cat', observed=True)[self.target].agg(['mean', 'median', 'count']).to_dict()
        if 'evento_macro' in df.columns:
            res["06_weather_impact"]["macro"] = df.groupby('evento_macro')[self.target].agg(['mean', 'median', 'count']).to_dict()

        # H7: Macro Binned
        macro_vars = ['smlv', 'trm', 'inflacion_mensual_ipc', 'tasa_desempleo']
        res["07_macro_impact"] = {}
        for var in [v for v in macro_vars if v in df.columns]:
            df[f'{var}_bin'] = pd.qcut(df[var], 4, labels=['Q1', 'Q2', 'Q3', 'Q4'], duplicates='drop')
            res["07_macro_impact"][var] = df.groupby(f'{var}_bin', observed=True)[self.target].agg(['mean', 'median', 'count']).to_dict()

        # H8: Periodos Refinados
        df['periodo'] = 'Post-Pandemia'
        df.loc[df.index < '2020-05-01', 'periodo'] = 'Pre-Pandemia'
        df.loc[(df.index >= '2020-05-01') & (df.index <= '2021-04-30'), 'periodo'] = 'Pandemia'
        df.loc[(df.index >= '2021-05-01') & (df.index <= '2022-12-31'), 'periodo'] = 'Reactivación'
        res["08_period_analysis"] = df.groupby('periodo')[self.target].agg(['mean', 'median', 'count']).to_dict()
        self._plot_box(df, 'periodo', self.target, "Demand by Historical Periods", "period_analysis_box")
        
        return res, df

    def _analyze_interactions(self, df):
        """Análisis de Interacciones (Heatmaps)."""
        self.logger.info("Analizando Interacciones Cruciales...")
        df = df.copy()
        df['is_weekend'] = df.index.dayofweek.isin([5, 6]).astype(int)
        df['is_weekend_str'] = df['is_weekend'].map({1: 'Finde', 0: 'Semana'})
        
        interactions = {}
        # Promo x Weekend
        if 'es_promocion' in df.columns:
            pivot = df.pivot_table(values=self.target, index='es_promocion', columns='is_weekend_str', aggfunc='mean')
            interactions["promo_weekend"] = pivot.to_dict()
            self._plot_heatmap(pivot, "Promo x Weekend Interaction", "interaction_promo_weekend")
        
        # Quincena x Rain
        if 'is_quincena' in df.columns and 'clima_cat' in df.columns:
            pivot = df.pivot_table(values=self.target, index='is_quincena', columns='clima_cat', aggfunc='mean')
            interactions["quincena_rain"] = pivot.to_dict()
            self._plot_heatmap(pivot, "Quincena x Rain Interaction", "interaction_quincena_rain")
            
        return interactions

    def _analyze_anomalies(self, df, resid):
        """
        Detección Estructural de Anomalías (Outliers).
        Identifica días con comportamiento atípico no explicado por festivos, promos o ciclos.
        """
        self.logger.info("Detectando y Caracterizando Anomalías (Outliers)...")
        df = df.copy()
        
        # 1. Definir umbral (3 sigma sobre el residuo de la descomposición)
        # Limpiar NaNs del residuo si existen
        resid_clean = resid.dropna()
        threshold = 3 * resid_clean.std()
        
        outliers_mask = resid_clean.abs() > threshold
        outliers_indices = resid_clean[outliers_mask].index
        
        # 2. Caracterización: ¿Explicado o Inexplicado?
        # Revisamos si el día outlier tiene algún flag activo
        explain_cols = ['es_festivo_co', 'es_promocion', 'is_quincena', 'is_novena', 'is_feria', 'is_prima']
        available_explain = [c for c in explain_cols if c in df.columns]
        
        df_outliers = df.loc[outliers_indices].copy()
        df_outliers['is_explained'] = df_outliers[available_explain].any(axis=1).astype(int)
        
        unexplained = df_outliers[df_outliers['is_explained'] == 0]
        explained = df_outliers[df_outliers['is_explained'] == 1]
        
        # 3. Clasificación por magnitud
        unexplained_high = unexplained[resid_clean.loc[unexplained.index] > threshold]
        unexplained_low = unexplained[resid_clean.loc[unexplained.index] < -threshold]
        
        results = {
            "summary": {
                "total_outliers": len(df_outliers),
                "explained_outliers": len(explained),
                "unexplained_anomalies": len(unexplained),
                "unexplained_positive_spikes": len(unexplained_high),
                "unexplained_negative_drops": len(unexplained_low)
            },
            "unexplained_dates": unexplained.index.strftime('%Y-%m-%d').tolist()
        }
        
        # 4. Visualización Premium
        fig, ax = plt.subplots(figsize=(15, 7))
        ax.plot(df.index, df[self.target], label='Demanda Real', color='slategray', alpha=0.6)
        
        if not explained.empty:
            ax.scatter(explained.index, explained[self.target], color='forestgreen', label='Outlier Explicado (Business Rules)', zorder=5)
        if not unexplained.empty:
            ax.scatter(unexplained.index, unexplained[self.target], color='crimson', marker='x', s=80, label='Anomalía Inexplicada (Ruido Estructural)', zorder=6)
            
        ax.set_title("Detección de Anomalías Estructurales (Target Variable)")
        ax.set_xlabel("Fecha")
        ax.set_ylabel("Unidades Vendidas")
        ax.legend()
        plt.grid(True, linestyle='--', alpha=0.3)
        self._save_figure(fig, "anomaly_detection")
        
        return results

    def _analyze_variance_stability(self, df):
        """
        Análisis de Estabilidad de la Varianza (Heterocedasticidad).
        Determina si el crecimiento del negocio ha aumentado la volatilidad (ruido).
        """
        self.logger.info("Analizando Estabilidad de la Varianza (Heterocedasticidad)...")
        df = df.copy()
        
        # 1. Volatilidad por Periodos Históricos
        periods = {
            "Pre-Pandemia": df[df['periodo'] == 'Pre-Pandemia'][self.target],
            "Pandemia": df[df['periodo'] == 'Pandemia'][self.target],
            "Reactivación": df[df['periodo'] == 'Reactivación'][self.target],
            "Post-Pandemia": df[df['periodo'] == 'Post-Pandemia'][self.target]
        }
        
        variance_stats = {}
        for name, series in periods.items():
            if not series.empty:
                variance_stats[name] = {
                    "std_dev": float(series.std()),
                    "coeff_variation": float(series.std() / series.mean()) if series.mean() != 0 else 0
                }
        
        # 2. Ratio de Estabilidad (Post vs Pre)
        pre_std = variance_stats.get("Pre-Pandemia", {}).get("std_dev", 1)
        post_std = variance_stats.get("Post-Pandemia", {}).get("std_dev", 1)
        volatility_ratio = post_std / pre_std
        
        # 3. Recomendación de Transformación
        # Si el Coeficiente de Variación es alto (> 0.3) o el ratio es > 1.5, sugerir log
        cv_post = variance_stats.get("Post-Pandemia", {}).get("coeff_variation", 0)
        needs_transform = bool(volatility_ratio > 1.5 or cv_post > 0.3)
        
        results = {
            "period_stats": variance_stats,
            "volatility_ratio_post_vs_pre": float(volatility_ratio),
            "recommendation": {
                "needs_transformation": needs_transform,
                "suggested_method": "Logarítmica o Box-Cox" if needs_transform else "Ninguna (Varianza Estable)"
            }
        }
        
        # 4. Visualización de Volatilidad Rolling (30 días)
        fig, ax = plt.subplots(figsize=(12, 6))
        rolling_std = df[self.target].rolling(window=30).std()
        ax.plot(df.index, rolling_std, label='Desviación Estándar Rolling (30d)', color='darkorange', linewidth=2)
        
        # Líneas verticales para separar periodos
        ax.axvline(pd.to_datetime('2020-05-01'), color='gray', linestyle='--', alpha=0.5)
        ax.axvline(pd.to_datetime('2021-05-01'), color='gray', linestyle='--', alpha=0.5)
        ax.axvline(pd.to_datetime('2023-01-01'), color='gray', linestyle='--', alpha=0.5)
        
        ax.set_title("Evolución de la Volatilidad de la Demanda (Rolling Std Dev)")
        ax.set_xlabel("Fecha")
        ax.set_ylabel("Std Dev (Unidades)")
        ax.legend()
        plt.grid(True, alpha=0.2)
        self._save_figure(fig, "variance_stability")
        
        return results

    def _analyze_frequencies(self, series):
        """
        Análisis de Frecuencia (Espectrograma / Periodograma).
        Detecta ciclos ocultos (frecuencias fantasma) en la demanda.
        """
        self.logger.info("Analizando Frecuencias (Periodograma)...")
        series_clean = series.dropna()
        
        # 1. Calcular Periodograma (Power Spectral Density)
        f, Pxx_den = signal.periodogram(series_clean, fs=1.0) # fs=1.0 para datos diarios
        
        # 2. Convertir frecuencias a periodos (días = 1/f)
        # Evitar división por cero
        with np.errstate(divide='ignore'):
            periods = 1.0 / f
            
        # 3. Filtrar picos significativos (Top 5)
        # Ignorar frecuencias muy bajas (tendencias de largo plazo > 365 días)
        mask = (periods > 2) & (periods <= 365)
        f_masked = f[mask]
        Pxx_masked = Pxx_den[mask]
        periods_masked = periods[mask]
        
        top_indices = np.argsort(Pxx_masked)[-5:][::-1]
        top_periods = {
            f"peak_{i+1}": {
                "period_days": float(periods_masked[idx]),
                "power": float(Pxx_masked[idx])
            } for i, idx in enumerate(top_indices)
        }
        
        # 4. Visualización Premium (Espectrograma)
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.semilogy(periods_masked, Pxx_masked, color='purple', linewidth=1.5)
        
        # Resaltar picos
        for i, idx in enumerate(top_indices):
            p = periods_masked[idx]
            ax.annotate(f"{p:.1f}d", xy=(p, Pxx_masked[idx]), xytext=(p+5, Pxx_masked[idx]*1.5),
                        arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=5))
        
        ax.set_title("Espectrograma de la Demanda (Análisis de Periodicidad)")
        ax.set_xlabel("Periodo (Días)")
        ax.set_ylabel("Densidad Espectral de Potencia (PSD)")
        ax.set_xlim(2, 60) # Enfocar en ciclos de corto/mediano plazo
        plt.grid(True, which="both", ls="-", alpha=0.2)
        self._save_figure(fig, "frequency_analysis")
        
        return {
            "top_periods": top_periods,
            "description": "Picos de potencia que indican ciclos recurrentes en días."
        }

    def _analyze_lead_lag(self, df):
        """
        NIVEL SUPERIOR: Análisis de Retardos (Lead/Lag).
        Estudia el efecto resaca y el impacto diferido de variables macro.
        """
        self.logger.info("Analizando Retardos (Lead/Lag Analysis)...")
        df = df.copy()
        results = {}
        
        # 1. Efecto Resaca/Anticipación (Autocorrelação Lags 1-7)
        lag_corrs = {f"lag_{i}": float(df[self.target].corr(df[self.target].shift(i))) for i in range(1, 8)}
        results["autocorrelation_lags"] = lag_corrs
        
        # Scatter Plot Target(t) vs Target(t-1)
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.scatter(df[self.target].shift(1), df[self.target], alpha=0.5)
        ax.set_xlabel("Demanda (t-1)")
        ax.set_ylabel("Demanda (t)")
        ax.set_title(f"Efecto Resaca: t vs t-1 (Corr: {lag_corrs['lag_1']:.2f})")
        self._save_figure(fig, "lag_scatter_t1")
        
        # 2. Análisis de Transiciones: Domingo -> Lunes
        df['day_name'] = df.index.day_name()
        sunday_to_monday = []
        for i in range(1, len(df)):
            if df.iloc[i-1]['day_name'] == 'Sunday' and df.iloc[i]['day_name'] == 'Monday':
                sunday_to_monday.append({
                    "sunday": float(df.iloc[i-1][self.target]),
                    "monday": float(df.iloc[i][self.target]),
                    "drop": float(df.iloc[i-1][self.target] - df.iloc[i][self.target])
                })
        if sunday_to_monday:
            sm_df = pd.DataFrame(sunday_to_monday)
            results["transition_sunday_monday"] = {
                "mean_sunday": float(sm_df['sunday'].mean()),
                "mean_monday": float(sm_df['monday'].mean()),
                "mean_drop": float(sm_df['drop'].mean()),
                "correlation": float(sm_df['sunday'].corr(sm_df['monday']))
            }

        # 3. Cross-Correlation (CCF) para Macro: TRM e IPC
        macro_vars = ['trm', 'inflacion_mensual_ipc']
        results["macro_lead_lag"] = {}
        
        for var in [v for v in macro_vars if v in df.columns]:
            # Calcular CCF hasta 30 días
            lags = list(range(31))
            ccf_values = [float(df[self.target].corr(df[var].shift(i))) for i in lags]
            results["macro_lead_lag"][var] = {
                "peak_correlation": float(max(ccf_values, key=abs)),
                "peak_lag": int(np.argmax(np.abs(ccf_values))),
                "ccf_values": {f"lag_{i}": v for i, v in enumerate(ccf_values)}
            }
            
            # Gráfico CCF
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.stem(lags, ccf_values)
            ax.set_title(f"Cross-Correlation: {var.upper()} vs Demanda (0-30 días)")
            ax.set_xlabel("Lag (días)")
            ax.set_ylabel("Correlación")
            self._save_figure(fig, f"ccf_{var}")

        return results

    def _plot_heatmap(self, pivot_df, title, name):
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.heatmap(pivot_df, annot=True, fmt=".2f", cmap="YlGnBu", ax=ax)
        plt.title(title)
        self._save_figure(fig, name)

    def _plot_box(self, df, x, y, title, name, order=None):
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.boxplot(data=df, x=x, y=y, order=order, hue=x, legend=False, palette="viridis", ax=ax)
        plt.title(title)
        plt.xticks(rotation=45)
        self._save_figure(fig, name)

    def _save_figure(self, fig, name):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fig.savefig(os.path.join(self.figures_path, f"history/{name}_{ts}.png"))
        fig.savefig(os.path.join(self.figures_path, f"{name}_latest.png"))
        plt.close(fig)

    def run(self):
        self.logger.info("--- Ejecutando Fase 03: EDA Integral (Interacciones + Lead/Lag) ---")
        master_path = os.path.join(self.config["general"]["data_cleansed_path"], "master_data.parquet")
        df_master = pd.read_parquet(master_path).sort_index()
        train_df, val_df, test_df = self._split_data(df_master)
        
        decomp = self._analyze_decomposition(train_df[self.target])
        stationarity = self._analyze_stationarity(train_df[self.target])
        autocorr = self._analyze_autocorrelation(train_df[self.target])
        multicol = self._analyze_multicollinearity(train_df)
        hypotheses, train_with_flags = self._validate_hypotheses(train_df)
        
        # Obtener residuo de la descomposición para anomalías
        decomposition_temp = seasonal_decompose(train_df[self.target].dropna(), model='additive', period=7)
        anomalies = self._analyze_anomalies(train_with_flags, decomposition_temp.resid)
        
        variance = self._analyze_variance_stability(train_with_flags)
        
        freqs = self._analyze_frequencies(train_df[self.target])
        
        interactions = self._analyze_interactions(train_with_flags)
        lead_lag = self._analyze_lead_lag(train_with_flags)
        
        report = {
            "phase": "03_eda",
            "timestamp": datetime.now().isoformat(),
            "description": "Reporte EDA Integral: Hipótesis, Interacciones, Anomalías, Estabilidad, Frecuencias y Lead/Lag.",
            "data_splits": {"train": len(train_df), "val": len(val_df), "test": len(test_df)},
            "statistical_audit": {
                "decomposition": decomp,
                "stationarity": stationarity,
                "autocorrelation": autocorr,
                "multicollinearity": multicol
            },
            "business_insights": hypotheses,
            "advanced_analytics": {
                "interaction_analysis": interactions,
                "anomaly_analysis": anomalies,
                "variance_stability": variance,
                "frequency_analysis": freqs,
                "lead_lag_analysis": lead_lag
            }
        }
        
        save_report(report, "phase_03_eda", self.reports_path)
        return report

if __name__ == "__main__":
    DataAnalyzer().run()
