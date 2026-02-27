# Blueprint de Ingeniería: Fase 02 - Data Preprocessing & Governance

Este documento define las **Leyes de Transformación** universales aplicadas al dataset. Su propósito es servir como estándar para convertir fuentes heterogéneas en una serie de tiempo unificada y perfecta para el modelado.

---

## 1. 🎯 Objetivos Estratégicos (Data Integrity)
*   **Single Source of Truth:** Unificar 6 fuentes de datos atomizadas en un **Master Dataset**.
*   **Perfección Cronológica:** Garantizar que no falte un solo segundo de la serie temporal.
*   **Tratamiento Determinista:** Aplicar reglas de imputación ciegas y replicables.

---

## 2. 🏗️ El Algoritmo de Consolidación (The Pipeline)
El procesador (`src/preprocessor.py`) ejecuta un flujo secuencial mandatorio de 5 pasos:

### Paso 1: Deduplicación y Pre-Limpieza
*   **Lógica de Versionalización:** Si existen dos registros para el mismo día, se prioriza el más reciente. Esto maneja errores de carga manual o re-procesos en base de datos.
*   **Fixing Contract Bugs:** Se corrigen errores de negocio conocidos (ej. ventas que no cuadran con promociones) antes de la unión.

### Paso 2: El "Master Join" (Broad Alignment)
*   Se utiliza un `outer join` sobre la columna `fecha`.
*   Se asegura que el Master Dataset tenga el rango de fechas total cubierto por todas las tablas.

### Paso 3: Reindexación Cronológica (Gap Healing)
*   **Crucial para Forecasting:** Se genera un índice de fechas diario continuo. 
*   Cualquier día que no existiera en las tablas originales se crea automáticamente, asegurando que los métodos de rezagos (Lags) trabajen sobre distancias temporales constantes.

### Paso 4: Reconstrucción de la Variable Objetivo
*   **Lógica:** `Demanda = Ventas Reales + Unidades Agotadas`.
*   Esta variable es la brújula del proyecto y se construye garantizando que no existan valores negativos.

---

## 3. 🛡️ Protocolo de Imputación Inteligente
No todos los nulos se tratan igual. Se definen tres leyes de imputación:

1.  **Ley de Inactividad (Cero-Fill):** Para variables de conteo (ventas, bonificadas, anuncios). Si no hay dato, se asume 0.
2.  **Ley de Permanencia (Forward-Fill):** Para variables de estado (precios, TRM, desempleo). El estado de hoy se mantiene hasta que el entorno cambie.
3.  **Ley de Continuidad (Interpolación):** Para variables físicas (temperatura, precipitación), suavizando los huecos mediante promedios locales.

---

## 4. ⚙️ Auditoría de Calidad Post-Procesamiento
Al finalizar, el sistema genera un reporte JSON que incluye:
*   **Shape Consistency:** Variación del número de registros antes y después de la reindexación.
*   **Null-Audit:** Certificación de que el `Master Dataset` tiene 0 valores nulos antes de pasar a la fase de EDA.
*   **Type Safety:** Verificación de que todos los tipos de datos son óptimos (Categorical vs Numeric).

---

## 5. 📂 Artefactos y Trazabilidad
*   **Silver Layer (Processed):** [master_data.parquet](file:///c:/Users/USUARIO/Documents/Forecaster/Tu_Bunuelito/data/02_cleansed/master_data.parquet)
*   **Reporte de Calidad:** [phase_02_preprocessing_latest.json](file:///c:/Users/USUARIO/Documents/Forecaster/Tu_Bunuelito/outputs/reports/phase_02/phase_02_preprocessing_latest.json)

---
> [!IMPORTANT]
> **Blueprint Lesson:** Nunca omitir la reindexación cronológica. Una serie de tiempo con "huecos" rompe la lógica matemática de los modelos de rezagos y estacionalidad.
