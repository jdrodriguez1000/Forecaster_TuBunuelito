---
name: pipeline_forecasting_manager
description: Gestiona la ejecución secuencial del pipeline de forecasting, asegurando la adherencia a la Metodología Production-First y los estándares de ciencia de datos.
---

# Skill: Gestor del Pipeline de Forecasting (Pipeline Manager)

Esta habilidad dirige el ciclo de vida de un proyecto de forecasting, desde la extracción de datos hasta la generación del pronóstico de negocio, garantizando que el código sea productivo desde su concepción.

## 🔄 Metodología de Ejecución (Production-First)
En cada fase técnica, el agente debe seguir obligatoriamente este flujo secuencial:

1.  **[CONFIG]**: Parametrización en `config.yaml`. Definición de rutas, hiperparámetros y reglas de negocio.
2.  **[CORE]**: Desarrollo de la lógica en archivos `.py` modulares dentro de `src/`.
3.  **[UNIT-TEST]**: Implementación y aprobación de pruebas unitarias en `tests/unit/`.
4.  **[ORCHESTRATE]**: Integración y desarrollo del flujo en el orquestador principal (ej. `main.py`).
5.  **[PROD-OUT]**: Ejecución en terminal para generar reportes y artefactos oficiales en `outputs/`.
6.  **[INTEGRATION-TEST]**: Validación de flujo completo y contratos E2E en `tests/integration/`.
7.  **[GEN-SCRIPT] (Opcional)**: Creación del script generador de notebooks en `scripts/`.
8.  **[LAB-WORKFLOW] (Opcional)**: Creación del workflow para generar el notebook de experimentación automatizado.
9.  **[CLOSE]**: Commit a GitHub y aprobación formal de la fase por parte del usuario.

## 🔬 Fases del Pipeline de Forecasting

### Fase 01: Data Discovery & Audit (Salud de Datos)
*   **Acción**: Conexión a la fuente de datos, carga inicial (o incremental) y auditoría de integridad.
*   **Controles Críticos**:
    *   **Data Contract**: Validar que las columnas y tipos de datos coincidan con lo definido en la configuración.
    *   **Mínimo Histórico**: Verificar que existan suficientes datos para capturar estacionalidad (ej. 36 meses o ciclos completos).
    *   **Salud Estadística**: Identificar nulos, valores centinela, duplicados y huecos temporales.
    *   **Integridad de Negocio**: Verificar consistencia interna de los datos y coherencia entre variables relacionadas.
*   **Resultados**: Reporte de salud de datos y almacenamiento en la capa de datos crudos (`data/01_raw/`).

### Fase 02: Preprocesamiento Robusto (Limpieza y Alineación)
*   **Acción**: Transformación de datos crudos en un dataset limpio y alineado temporalmente.
*   **Controles Críticos**:
    *   **Estandarización**: Formateo de nombres (snake_case) y tipos de datos correctos.
    *   **Reindexación Temporal**: Asegurar una frecuencia continua (Diaria, Mensual, etc.) sin saltos en el tiempo.
    *   **Imputación Lógica**: Aplicar reglas de negocio o heurísticas estadísticas para llenar huecos (NaN).
    *   **Anti-Data Leakage**: Eliminar periodos incompletos o sospechosos que puedan sesgar el entrenamiento.
    *   **Agregación**: Resample del dataset a la frecuencia requerida por el objetivo de pronóstico.
*   **Resultados**: Dataset maestro en la capa de datos limpios (`data/02_cleansed/`).

### Fase 03: EDA (Análisis Exploratorio de Datos)
*   **Acción**: Análisis profundo orientado al modelado bajo el principio **"Ojos solo en el Pasado"**.
*   **Controles Críticos**:
    *   **Segmentación**: Análisis exclusivo sobre el set de entrenamiento (Train) para evitar fuga de información.
    *   **Estacionariedad**: Ejecución de pruebas estadísticas de raíces unitarias (ej. ADF - Dickey-Fuller).
    *   **Patrones**: Descomposición estacional y análisis de autocorrelación (ACF/PACF).
    *   **Atípicos**: Identificación y tratamiento de outliers y eventos de choque externos.
*   **Resultados**: Insights de modelado y figuras de soporte en `outputs/figures/` o `experiments/`.

### Fase 04: Feature Engineering (Enriquecimiento y Exógenas)
*   **Acción**: Creación de variables explicativas y proyecciones del horizonte futuro.
*   **Controles Críticos**:
    *   **Variables Deterministas**: Creación de indicadores basados en el calendario, ciclos y eventos conocidos.
    *   **Exógenas Futuras**: Implementación obligatoria de lógica de proyección para todas las variables externas que alimentarán el modelo en el horizonte de predicción.
    *   **Nota Técnica**: La creación de *Lags* y *Window Features* se delega generalmente a la configuración del modelo de series de tiempo.
*   **Resultados**: Dataset enriquecido en la capa de variables (`data/03_features/`).

### Fase 05: Modelado (Optimización y Selección)
*   **Acción**: Entrenamiento competitivo de algoritmos, búsqueda de hiperparámetros y selección del mejor modelo.
*   **Controles Críticos**:
    *   **Tournament**: Competencia entre modelos candidatos contra un modelo de referencia (Baseline).
    *   **Backtesting**: Evaluación mediante validación cruzada temporal o esquemas de ventana rodante.
    *   **Ljung-Box Test**: Ejecución obligatoria de la prueba de Ljung-Box sobre los residuos del modelo para validar independencia (white noise) y asegurar que se ha capturado toda la información de la serie.
    *   **Diagnóstico Residencial**: Análisis visual de residuos para detectar patrones no capturados o sesgos sistemáticos.
    *   **Champion Model**: Identificación y exportación del modelo con mejor desempeño técnico y estadístico.
*   **Resultados**: Reporte de experimentos y modelo pre-seleccionado en `outputs/models/`.

### Fase 06: Pronóstico (Producción y Entrega)
*   **Acción**: Ejecución del modelo seleccionado para la generación de predicciones futuras.
*   **Controles Críticos**:
    *   **Inferencia**: Generación de predicciones puntuales sobre el horizonte definido por el negocio.
    *   **Incertidumbre**: Cálculo de intervalos de confianza o bandas de probabilidad.
    *   **Métricas de Desempeño**: Cálculo final de error esperado (MAE, MAPE, RMSE) basado en el set de hold-out o validación final.
    *   **Post-procesamiento**: Aplicación de reglas de negocio para la limpieza o ajuste de los valores pronosticados antes de su exportación.
*   **Resultados**: Archivo de pronóstico final en `outputs/forecast/`.

### Fase 07: Simulación (Escenarios What-if)
*   **Acción**: Evaluación del comportamiento de la demanda bajo cambios hipotéticos en las variables exógenas.
*   **Controles Críticos**:
    *   **Baseline vs Scenario**: Comparación entre el pronóstico estándar (sin condiciones) y el pronóstico bajo la condición de la pregunta de negocio.
    *   **Impacto de Exógenas**: Sensibilidad del modelo ante la alteración controlada de variables predictoras (ej. cambios en precios, promociones, marketing o clima).
    *   **Respuestas al Negocio**: Generación de insights prácticos basados en la comparación de escenarios.
*   **Resultados**: Reporte de simulación y comparativa de escenarios en `outputs/simulations/`.

### Fase 08: Monitoreo (Salud y Retraining)
*   **Acción**: Seguimiento continuo del desempeño del modelo en producción frente a datos reales nuevos.
*   **Controles Críticos**:
    *   **Model Drift**: Detección de degradación en la precisión del modelo a medida que transcurre el tiempo.
    *   **Alertas de Reentrenamiento**: Definición de umbrales para decidir si el modelo sigue siendo válido, requiere reajuste de parámetros o debe ser cambiado por completo.
    *   **Integridad Post-Prod**: Validación de que las entradas de datos actuales mantienen la distribución observada durante el entrenamiento.
*   **Resultados**: Dashboard o reporte periódico de salud del modelo en `outputs/monitoring/`.

## 📊 Protocolo de Trazabilidad
Cada fase debe generar un artefacto (ej. JSON) bajo el **Patrón de Persistencia Dual** (Versión `latest` en raíz y versiones históricas en subcarpeta `history/`) incluyendo:
*   `phase`: Nombre de la fase.
*   `timestamp`: Fecha y hora de ejecución.
*   `metrics`: Resultados clave o KPIs de la fase.
*   `description`: Resumen técnico de la ejecución.
*   `status`: Resultado de las validaciones y pruebas relacionadas.
