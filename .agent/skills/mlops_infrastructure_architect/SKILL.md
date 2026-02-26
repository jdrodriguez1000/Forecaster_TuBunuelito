---
name: mlops_infrastructure_architect
description: Define los estándares de ingeniería, jerarquía de almacenamiento y protocolos de calidad para asegurar que los proyectos de forecasting sean reproducibles, modulares y auditables bajo la metodología Production-First.
---

# Skill: Arquitecto de Infraestructura MLOps (Forecasting Genérico)

Esta habilidad define el ecosistema técnico, la jerarquía de almacenamiento y los protocolos de calidad para cualquier proyecto de pronóstico de series de tiempo. Su objetivo es garantizar que la transición del experimento a la producción sea fluida, auditable y libre de errores de refactorización.

## 📂 1. Estándar de Almacenamiento (Data Layers)
Garantiza la inmutabilidad y el orden del flujo de datos a través de capas lógicas:

*   **`data/01_raw/`**: Datos crudos obtenidos directamente de la fuente original (API, DB, CSV). Inmutables.
*   **`data/02_cleansed/`**: Datos tras limpieza inicial, estandarización de esquemas (snake_case), tipos de datos y manejo de nulos/duplicados.
*   **`data/03_features/`**: Datasets enriquecidos con ingeniería de variables (estacionalidades, calendarios, exógenas y proyecciones de horizonte).
*   **`data/04_processed/`**: Dataset final listo para el entrenamiento del modelo (frecuencia alineada y variables filtradas).

## 🏗️ 2. Metodología de Trabajo Industrializada (Production-First)
El pilar fundamental: la lógica de producción es la base y los notebooks son extensiones para validación visual.

1.  **Configuración ([CONFIG]):** Todo cambio nace en `config.yaml`. Prohibido el uso de valores "hardcoded".
2.  **Core Técnico ([CORE]):** Desarrollo de lógica modular, clases y funciones en `src/`.
3.  **Pruebas Unitarias ([UNIT-TEST]):** Validación de componentes atómicos en `tests/unit/`.
4.  **Orquestación ([ORCHESTRATE]):** Integración en el flujo principal (ej. `main.py`).
5.  **Salidas Oficiales ([PROD-OUT]):** Generación de reportes JSON y artefactos en `outputs/`.
6.  **Pruebas de Integración ([INTEGRATION-TEST]):** Validación de flujos E2E en `tests/integration/`.
7.  **Automatización Lab ([GEN-SCRIPT]) (Opcional):** Creación de scripts generadores de notebooks en `scripts/`.
8.  **Workflow Lab ([LAB-WORKFLOW]) (Opcional):** Automatización de la regeneración de notebooks de validación.
9.  **Cierre ([CLOSE]):** Documentación, auditoría de resultados y commit final.

## 💻 3. Arquitectura de Código (`src/`)
Diseño orientado a objetos y modularidad:

1.  **`src/connectors/`**: Clientes de conexión a datos (DB, Cloud, APIs).
2.  **`src/loader.py`**: Extracción y validación de contratos de datos.
3.  **`src/preprocessor.py`**: Limpieza, reindexación temporal e imputación lógica de nulos.
4.  **`src/features.py`**: Ingeniería de variables (Calendario, Exógenas, Flags de Negocio).
5.  **`src/models.py`**: Definición de clases para entrenamiento, optimización de hiperparámetros y selección de modelos.
6.  **`src/forecaster.py`**: Lógica de generación de pronósticos, intervalos de confianza e inferencia.
7.  **`src/simulator.py`**: Implementación de escenarios "What-if" y análisis de sensibilidad.
8.  **`src/monitor.py`**: Métricas de salud del modelo y detección de degradación (Drift).
9.  **`src/utils/`**: Helpers para logging, exportación JSON y utilidades del sistema.

## ✅ 4. Capa de Calidad y QA (`tests/`)
Protocolos de validación obligatorios usando `pytest`:
*   **Tests Unitarios**: En `tests/unit/` para lógica atómica y contratos de módulos.
*   **Tests de Integración**: En `tests/integration/` para flujos E2E y persistencia de datos.
*   **Trazabilidad de Pruebas**: Todo resultado de ejecución de pruebas debe generar un reporte JSON en `tests/reports/` siguiendo el **Protocolo de Dual Persistencia**.

## 📊 5. Segregación de Salidas y Protocolo de Trazabilidad

### 🏭 Producción (`outputs/`) y Calidad (`tests/reports/`)
Toda salida oficial debe seguir el **Protocolo de Dual Persistencia**:
*   **`tests/reports/`**: Logs y resultados de ejecución de pruebas unitarias e integración.
*   **`outputs/reports/`**: Reportes JSON. Versión `latest.json` en raíz y versiones con timestamp en `history/`.
*   **`outputs/figures/`**: Visualizaciones y artefactos gráficos oficiales (PNG/HTML).
*   **`outputs/models/`**: Binarios de modelos (`.pkl`, `.joblib`).
*   **`outputs/forecast/`**: Pronóstico diario/mensual en formato CSV.
*   **`outputs/simulations/`**: Resultados de análisis de escenarios competitivos.
*   **`outputs/monitoring/`**: Reportes de salud y drift del modelo.

### 🔬 Laboratorio (`experiments/`)
*   Resultados transitorios de ejecución de Notebooks. No deben mezclarse con artefactos de producción.
*   `experiments/phase_0X_name/artifacts/` y `experiments/phase_0X_name/figures/`.

## ⚙️ 6. Estándares de Configuración y Entorno
*   **Zero Hardcoding**: Todo parámetro (rutas, horizonte, semillas, KPIs) reside en `config.yaml`.
*   **Estructura Jerárquica**: El archivo `config.yaml` debe estar organizado por bloques lógicos según las fases del pipeline.
*   **Aislamiento**: Uso estricto de `.venv` y gestión de dependencias en `requirements.txt`.
*   **Seguridad**: Credenciales sensibles gestionadas vía `.env` (nunca commiteadas).
