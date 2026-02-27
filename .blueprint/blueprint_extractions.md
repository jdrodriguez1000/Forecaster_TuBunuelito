# Blueprint de Ingeniería: Fase 01 - Data Extraction & Synchronization (Loader)

Este documento no solo registra el resultado, sino que sirve como la **Guía Maestra de Ingeniería** para replicar la ingesta incremental de datos en cualquier proyecto de series de tiempo bajo el estándar de Sabbia Solutions.

---

## 1. 🎯 Objetivos Estratégicos (The North Star)
*   **Eficiencia de Ancho de Banda:** Cargar solo lo necesario (delta incremental).
*   **Inmutabilidad del Dato Crudo:** Preservar la fuente de verdad en `/data/01_raw/`.
*   **Certificación Automática:** Ninguna tabla entra al pipeline sin pasar el "Data Contract".

---

## 2. 🏗️ Arquitectura del Motor de Ingesta (Logic Path)
El motor de extracción (`src/loader.py`) opera bajo una lógica de **High Water Mark**:

1.  **State Detection:** El sistema inspecciona los metadatos de los archivos Parquet locales. La fecha máxima detectada se convierte en el `start_date` para la consulta SQL.
2.  **Supabase Bridge:** Se utiliza un cliente `Realtime` y `Postgres` para realizar el fetch de los registros faltantes.
3.  **Merge & Persistence:**
    *   Si no hay datos locales, realiza una **Full Extraction**.
    *   Si hay datos locales, realiza un **Append** de los nuevos registros.
    *   **Formato de Salida:** Parquet (proporciona compresión y preserva el esquema de tipos de datos de base).

---

## 3. 🛡️ Protocolo de Validación "Zero-Trust"
Para asegurar que el proyecto no sea contaminado con datos corruptos, cada extracción ejecuta:

*   **Atomic Audit:** Verificación de tipos (Integer vs Float) y nombres de columnas contra el `config.yaml`.
*   **Integridad de Serie (Gap Check):** Algoritmo que detecta discontinuidades en las fechas. Si faltan días, el reporte JSON emite una alerta crítica.
*   **Profiling Cuantílico:** Se genera un perfil de 7 puntos (`min, p25, p50, p75, max, mean, std`) para detectar si los datos recién llegados se desvían drásticamente del comportamiento histórico (detección de deriva de datos).

---

## 4. ⚙️ Configuración y Orquestación (Reusable Blueprint)
Toda la lógica de extracción es agnóstica a la tabla gracias a la parametrización en `config.yaml`:
*   **Rutas de Almacenamiento:** Centralizadas para evitar *hardcoding*.
*   **Esquemas Definidos:** El contrato de datos está escrito en YAML, permitiendo cambiar el origen de datos sin tocar el código Python.

---

## 5. 📂 Artefactos y Trazabilidad (Protocolo Dual)
*   **Data Lake (Raw):** Archivos `.parquet` en `data/01_raw/`.
*   **Bitácora Técnica:** [phase_01_extractions_latest.json](file:///c:/Users/USUARIO/Documents/Forecaster/Tu_Bunuelito/outputs/reports/phase_01/phase_01_extractions_latest.json)

---
> [!NOTE]
> **Best Practice Reusable:** El uso de archivos Parquet permite que este loader sea compatible con herramientas de Big Data (Spark/Dask) en el futuro si el volumen de datos escala.
