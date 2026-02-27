---
trigger: always_on
---

# Project Rules: Tu Buñuelito Forecasting

Este archivo constituye la autoridad máxima de restricciones cognitivas y técnicas para el proyecto. Todo agente o colaborador debe asegurar el cumplimiento estricto de estas reglas antes de ejecutar cualquier Skill o Workflow.

---

## 1. 🎯 Restricciones de Dominio y Negocio
*   **Consultora:** Sabbia Solutions & Services SAS (Triple S).
*   **Cliente:** Cafetería SAS.
*   **Marca/Producto:** Tu Buñuelito / El Buñuelo (Producto Estrella).
*   **Variable Objetivo:** Demanda diaria de buñuelos (calculada/reconstruida a partir de unidades vendidas y unidades agotadas).
*   **Regla de Oro (Anti-Data Leakage):** 
    *   **Temporalidad**: El entrenamiento y procesamiento de features (lags) para predecir el día $T$ deben detenerse estrictamente en el cierre del día $T-1$. Queda prohibido el uso de información parcial o total del día en curso para predecir resultados de ese mismo día.
    *   **Atomicidad**: Prohibido el uso de variables exógenas que sean resultado de operaciones matemáticas con la variable objetivo del mismo periodo temporal. Solo se permiten variables "atómicas" independientes.
*   **Horizonte de Predicción:** El sistema debe generar siempre un pronóstico continuo y estricto a nivel **diario** para los próximos **185 días**. Posteriormente, en la capa de reportes, los resultados se agruparán mensualmente fusionando el mes actual (Ventas Reales + Predicción) y descartando visualmente cualquier mes calendario final que no esté cubierto al 100% por el horizonte (para evitar gráficos de meses incompletos).
*   **Métricas de Éxito:** El modelo final es válido si supera a los métodos actuales y mantiene un **MAPE < 12%** en el set de validación/prueba.

## 2. 🏗️ Arquitectura de Software y Estándares
*   **Sincronía y Verdad del Proyecto:** Para cada paso de ejecución, el sistema debe auditar obligatoriamente los archivos `project_charter.md`, `project_rules.md` y las habilidades (`.agent/skills/`) creadas. Asimismo, debe verificar el estado actual de `config.yaml` para garantizar que el conocimiento esté actualizado y evitar el uso de valores "hardcoded" (quemar datos).
*   **Estrategia de Modelado:** Uso obligatorio de la librería `skforecast` mediante la estrategia de Pronóstico Directo (`ForecasterDirect`).
*   **Batería de Modelos Autorizados:** Solo se permite la experimentación y optimización competitiva entre:
    *   `Ridge`, `RandomForestRegressor`, `LGBMRegressor`, `XGBRegressor`, `GradientBoostingRegressor` y `HistGradientBoostingRegressor`.
*   **Configuración:** Prohibido el uso de valores "hardcoded". Rutas, hiperparámetros, fechas de corte, nombres de variables y otros deben residir estrictamente en `config.yaml`. Este archivo debe seguir una estructura jerárquica estricta por fases:
    1.  `general`: Parámetros globales (semillas, rutas base).
    2.  `extractions`: Carga inicial de datos desde Supabase.
    3.  `preprocessing`: Limpieza, control temporal, agrupaciones y manejo de nulos.
    4.  `eda`: Visualizaciones, análisis de estacionariedad e insights.
    5.  `features`: Ingeniería de variables (rezagos, estacionalidad, promociones, clima) y proyecciones.
    6.  `modeling`: Entrenamiento, configuración de modelos, métricas y backtesting.
*   **Idioma:** Código (funciones, clases, variables) y estructura de archivos en **Inglés**; contexto, documentación markdown y reglas de negocio en **Español**.
*   **Persistencia:** La fuente de verdad histórica es **Supabase (PostgreSQL)**. Tablas a utilizar: `ventas`, `inventario`, `finanzas`, `marketing`, `macroeconomia`, `clima`.
*   **Carga de Datos:** La ingesta de información desde la base de datos debe contemplar lógicas que prevengan descargas repetitivas innecesarias, prefiriendo sincronizaciones o cargas incrementales hacia la capa local `/data/01_raw/`.

## 3. 🔬 Rigor en Ciencia de Datos y Validación
*   **Estrategia de Partición (Backtesting):** Se debe aplicar validación cruzada temporal (Time Series Cross Validation) o Partición Secuencial, asegurando siempre que se disponga de un escenario ciego equivalente a los **185 días** operativos.
*   **Tratamiento de Exógenas Futuras:** Las variables macroeconómicas o climáticas para el horizonte continuo al futuro (**185 días**) deben ser proyectadas utilizando heurísticas válidas de negocio, promedios móviles, o asumiendo permanencias razonables (Forward Fill).
*   **Lógica de Negocio (Features Obligatorias):**
    *   **Pandemia (Anomalía):** Crear flag para el periodo crítico (`1 de mayo de 2020` al `30 de abril de 2021`).
    *   **Promociones (2x1):** Crear flags para los meses de abril-mayo (`Abr-May`) y septiembre-octubre (`Sep-Oct`) activos desde el año 2022.
    *   **Novenas Navideñas:** Incremento en demanda para el ciclo del `16 al 26 de Diciembre`.
    *   **Ferias y Semana Santa:** Actividad de Domingo en Feria de las Flores (`01 al 10 de Agosto`) y Semana Santa (`Jueves y Viernes Santo`).
    *   **Días Festivos:** Deben ser tratados con un peso/importancia asimilado a un día **Sábado**.
    *   **Patrones de Pago:** Marcar Quincenas (`15-16` y `30-31 del mes`) y fechas de Prima Legal (`15 al 20 de Junio y Diciembre`).
    *   **Clima:** Separar entre lluvia ligera (efecto positivo) y lluvia fuerte (efecto negativo).
    *   **Marketing (Ads):** Activación 20 días antes de promoción, apagándose el día 25 del mes en que acaba la promoción.
*   **Reproducibilidad:** Se debe garantizar un comportamiento determinista utilizando la semilla global obligatoria `random_state=42`.

## 4. 🛠️ Protocolo de Integridad y Verdad de Datos
Para garantizar un desempeño pulcro en las series de tiempo, se aplican estas leyes de limpieza obligatorias:
*   **Fechas o Filas Duplicadas:** Si existen múltiples registros para una misma fecha u operación en Supabase, se conserva la **última actualización** y se descartan las previas.
*   **Continuidad Temporal (Reindexación diaria):** La serie de tiempo maestra debe ser cronológicamente perfecta día a día. Si falta un registro para una fecha específica, este debe ser **creado inicialmente con valores nulos (NaN)**. Posteriormente, en la etapa de **preprocesamiento**, se realizará la validación e imputación de dichos valores faltantes (ej. ceros para ventas, interpolación/ffill para macro o clima) antes de la creación de los *Lags*.

## 5. ⚙️ Metodología de Trabajo Industrializada (Production-First)
Se adopta un enfoque lineal "Lab-to-Prod", pero garantizando que los Core Modules dominen la operación:

1.  **Configuración y Parametrización ([CONFIG]):** Todo parámetro vive en `config.yaml`.
2.  **Desarrollo del Core Técnico ([CORE]):** Lógica, clases y procesamiento desarrollados en `/src/`.
3.  **Pruebas Unitarias ([UNIT-TEST]):** Aprobación mandatoria de tests en `tests/unit/` verificando transformadores atómicos.
4.  **Orquestación de Producción ([ORCHESTRATE]):** Integración del script generalizador `main.py` por fase.
5.  **Generación Oficial ([PROD-OUT]):** Toda orden de producción genera material inmutable en `outputs/`.
6.  **Automatización de Laboratorio ([GEN-SCRIPT]):** Se crean scripts `scripts/gen_XX.py` que importan de `src/` y arman notebooks transitorios.
7.  **Despliegue Experimental ([LAB-WORKFLOW]):** En la carpeta `notebooks/` se ejecutan y validan datos mediante exploración interactiva.
8.  **Cierre y Auditoría ([CLOSE]):** Generación del Informe Ejecutivo en `.docs/`, Git Commit y formalidad de cierre del hito.

## 6. 📄 Documentación Obligatoria por Fase (Blueprint & Executive Report)
Para garantizar la trazabilidad estratégica y técnica, cada fase del proyecto debe generar dos artefactos documentales mandatorios:

### 6.1. Blueprint de Fase (El Mapa Técnico)
*   **Ubicación:** `.blueprint/blueprint_phase_XX.md`
*   **Momento:** Se crea **antes** de iniciar el desarrollo técnico de la fase.
*   **Contenido:** Objetivos técnicos, arquitectura de datos, lógica de transformación planeada, métricas a monitorear y justificación de las variables/modelos a utilizar.

### 6.2. Informe Ejecutivo de Impacto (La Verdad Estratégica)
*   **Ubicación:** `.docs/executive_report_phase_XX.md`
*   **Momento:** Se crea **después** de completar la ejecución oficial y las pruebas de la fase.
*   **Estatus:** Debe ser aprobado por el usuario antes de avanzar a la siguiente fase.
*   **Estructura Obligatoria:** El informe debe dividirse en "Puntos de Poder" (Positivos) y "Verdades Críticas" (Riesgos/Advertencias), siguiendo estrictamente este formato para cada punto:
    *   **Nombre:** Título corto y descriptivo del hallazgo.
    *   **Frase:** Sentencia profesional y crítica que resume el impacto (estilo "píldora de verdad").
    *   **Justificación:** Párrafo pedagógico y gerencial explicando el "porqué" y la implicación de negocio.
    *   **Evidencia:** El dato numérico o estadístico exacto que respalda el punto.
    *   **Fuente:** Ubicación exacta del dato (ej: `outputs/reports/phase_03/phase_03_eda_latest.json` -> campo X).

## 7. 📂 Segregación de Salidas (Ambientes Lab vs. Prod)
Queda estrictamente prohibido mezclar salidas "experimentales" transitorias con salidas "Producción":
*   **Entorno Lab (Notebooks y Jupyter):** 
    *   Los reportes JSON nacidos de notebook van a `experiments/phase_0X_name/artifacts/`.
    *   Las figuras gráficas de exploración van a `experiments/phase_0X_name/figures/`.
*   **Entorno Prod (Ejecuciones CLI de main.py):**
    *   Los reportes JSON oficiales se mandan a `outputs/reports/phase_0X/`.
    *   Figuras oficiales en `outputs/figures/`.
    *   Modelos compilados (.pkl/.joblib) en `outputs/models/`.
    *   Archivos de pronóstico diario (.csv) en `outputs/forecast/`.
*   **Entorno Calidad (Pruebas Automatizadas):**
    *   Los reportes JSON de ejecución de pruebas van a `tests/reports/`.
*   **Aislamiento de Pruebas:** Los entornos de Test no pueden tocar artefactos reales. Todo framework de simulación y test local corre bajo un flag de Mocking o `save=False` aislando los datos.

## 9. 📤 Protocolo de Entregables y Trazabilidad
*   **Protocolo de Dual Persistencia (Trazabilidad Total):** Todo artefacto generado en producción o calidad (JSON de reportes, figuras PNG/HTML, modelos PKL/JOBLIB, pronósticos CSV y **reportes de pruebas**) debe seguir obligatoriamente este patrón:
    *   **Versión Histórica Inmutable:** Se guarda en una subcarpeta llamada `history/` con el formato `nombre_YYYYMMDD_HHMMSS.extension`.
    *   **Versión Puntero (Latest):** Se guarda en la raíz de su carpeta correspondiente (`reports/`, `figures/`, `models/`, `forecast/`, `tests/reports/`) como `nombre_latest.extension`.
    *   **Contenido de Reportes:** Los archivos JSON deben incluir siempre los campos `phase`, `timestamp`, `description` y las `metrics` de auditoría correspondientes (o resultados de pruebas).
*   **Gestión de Entornos:** Prohibida la instalación desorganizada de paquetes. Todo control reside en usar un solo `.venv` referenciado por `requirements.txt`.
*   **Gatekeeper:** El avance hacia una nueva fase queda denegado hasta que el usuario humano audite los reportes JSON, lea el **Informe Ejecutivo** correspondiente e introduzca su aprobación explícitamente en el chat.
