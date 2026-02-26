---
description: Inicializa la infraestructura física del proyecto (directorios, archivos base y entorno virtual) siguiendo los estándares de la habilidad mlops_infrastructure_architect.
---

# Workflow: Inicialización del Proyecto de Forecasting (Bootstrap Wizard)

Este flujo de trabajo es responsable de la creación física de la infraestructura del proyecto. Su objetivo es asegurar que la jerarquía de directorios y los archivos base cumplan estrictamente con los estándares definidos en la habilidad de Arquitectura MLOps y soporte las 8 fases del pipeline.

// turbo-all

## 🛠️ Pasos de Ejecución (Setup Inicial)

### Paso 1: Creación de la Estructura de Directorios
1. Generar la jerarquía de carpetas definida en el Skill `mlops_infrastructure_architect`:
    * `data/01_raw`, `data/02_cleansed`, `data/03_features`, `data/04_processed`
    * `notebooks/`, `scripts/`, `src/connectors/`, `src/utils/`, `tests/unit/`, `tests/integration/`
    * `experiments/phase_01_discovery/artifacts`, `experiments/phase_01_discovery/figures`
    * `experiments/phase_02_preprocessing/artifacts`, `experiments/phase_02_preprocessing/figures`
    * `experiments/phase_03_eda/figures`
    * `experiments/phase_04_features/artifacts`, `experiments/phase_04_features/figures`
    * `experiments/phase_05_modeling/artifacts`, `experiments/phase_05_modeling/figures`
    * `experiments/phase_06_forecast/artifacts`, `experiments/phase_06_forecast/figures`
    * `experiments/phase_07_simulations/artifacts`, `experiments/phase_07_simulations/figures`
    * `experiments/phase_08_monitoring/artifacts`, `experiments/phase_08_monitoring/figures`
    * `outputs/models/history`, `outputs/figures/history`, `outputs/forecast/history`, `outputs/reports/history`, `outputs/simulations/history`, `outputs/monitoring/history`

### Paso 2: Despliegue de Archivos Base (Scaffolding)
1. Crear los archivos base en `src/`, `scripts/` y raíz:
    * `src/connectors/db_connector.py` (Conexión a Supabase/PostgreSQL).
    * `src/loader.py` (Lógica de extracción y contratos).
    * `src/preprocessor.py` (Limpieza, reindexación cotidiana e imputación).
    * `src/features.py` (Ingeniería de variables exógenas y calendario).
    * `src/models.py` (Definición y entrenamiento de modelos con skforecast).
    * `src/forecaster.py` (Lógica de inferencia y generación de pronóstico).
    * `src/simulator.py` (Manejo de escenarios "What-if").
    * `src/monitor.py` (Métricas de salud y detección de drift).
    * `src/utils/helpers.py` (Helpers para Dual Persistencia y Logging).
    * `src/utils/config_loader.py` (Cargador de config.yaml).
    * `scripts/gen_discovery.py` (Generador de notebook para Fase 01).
    * `main.py` (Orquestador central del pipeline).
    * `.env.example` y `.env` (Gestión de credenciales).

### Paso 3: Configuración y Control
1. Crear un `config.yaml` inicial con la estructura jerárquica por fases (general, extractions, preprocessing, eda, features, modeling, forecast, simulations, monitoring).
2. Generar un `requirements.txt` con las librerías: `skforecast`, `pandas`, `numpy`, `python-dotenv`, `pyyaml`, `scikit-learn`, `matplotlib`, `seaborn`, `xgboost`, `lightgbm`, `papermill`, `pytest`, `sqlalchemy`, `psycopg2-binary`.
3. Crear un `.gitignore` estándar para Python que incluya `.venv`, `.env`, `data/`, `outputs/**/history/`, y archivos de caché.

### Paso 4: Configuración del Entorno Python
1. Validar la versión de Python (Recomendada: **3.12.x**).
2. Crear entorno virtual: `python -m venv .venv`.
3. Instalar dependencias: `pip install -r requirements.txt`.

### Paso 5: Validación Final
1. Verificar que toda la nomenclatura esté en **Inglés**.
2. Confirmar que el proyecto cumple con la regla de **Sincronía y Verdad** (revisar Charter y Rules).
3. Confirmar que el proyecto está listo para iniciar la **Fase 1: Data Discovery & Audit**.

---

## 🚦 Salida Esperada
Un ecosistema técnico listo, con entorno virtual configurado y estructura de carpetas que soporta el ciclo de vida completo del modelo de Tu Buñuelito.
