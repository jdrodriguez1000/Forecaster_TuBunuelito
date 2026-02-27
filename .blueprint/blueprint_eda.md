# Blueprint de Ciencia de Datos: Fase 03 - Machine Learning Exploratory Data Analysis (EDA)

Este blueprint detalla la **Batería de Pruebas Analíticas** avanzada diseñada para certificar la viabilidad de una serie de tiempo. Su enfoque es "Production-First", asegurando que cada insight descubierto sea una pieza de información accionable para la ingeniería de variables.

---

## 1. 🎯 Objetivos Estratégicos (Analytical rigor)
*   **Certificación Estadística:** Validar estacionariedad y ciclos dominantes.
*   **Descubrimiento de Lógicas Ocultas:** Identificar interacciones y retardos (Lags) óptimos.
*   **Blindaje contra Ruido:** Caracterizar y segregar anomalías estructurales.

---

## 2. 🏗️ El Framework de Análisis (Analytical Battery)
El analizador (`src/analyzer.py`) ejecuta una serie de experimentos modulares:

### A. Auditoría de Fundamentos (Integrity Check)
1.  **Descomposición Triple:** Separación de Tendencia (Trend), Estacionalidad (Seasonal - T=7) y Residuo (Residuals).
2.  **Test de Estacionariedad (ADF):** Prueba de Dickey-Fuller Aumentado para validar si la media y varianza son constantes en el tiempo.
3.  **Análisis de Memoria (ACF/PACF):** Identificación de correlaciones consigo misma en el pasado para definir la profundidad de los rezagos.

### B. Análisis de Interacciones Cruciales (Heatmaps)
No analizamos variables aisladas. El blueprint exige el cruce de dimensiones:
*   **Eventos vs Calendario:** Ej. Impacto de Promociones en Fines de Semana vs Días Laborables.
*   **Poder Adquisitivo vs Clima:** Ej. Cómo la Quincena mitiga la caída de ventas por lluvia.

### C. Ingeniería de Retardos (Lead/Lag Analysis)
*   **Efecto "Resaca" (Hangover):** Evaluar si un pico de ventas hoy causa una caída proporcional mañana (canibalización temporal).
*   **Cross-Correlation (CCF):** Determinar el desfase exacto (ej. 30 días) entre cambios en variables MACRO (TRM/IPC) y el impacto en la demanda.

### D. Detección de Anomalías Estructurales
*   **Algoritmo:** Basado en $3\sigma$ (3 desviaciones estándar) sobre el Residuo de la descomposición.
*   **Clasificación:** El sistema cataloga outliers en "Explicados" (Festivos/Promos) e "Inexplicados" (Anomalías puras). Esto permite limpiar el dataset de entrenamiento sin perder señal de negocio.

### E. Análisis Espectral (Frequency Analysis)
*   **Método:** Periodograma de Densidad Espectral de Potencia (PSD).
*   **Propósito:** Detectar "Ciclos Fantasma" no evidentes. Identificamos señales cada 90 días (trimestral) y 180 días (semestral), cruciales para modelos de largo plazo.

---

## 3. 🛡️ Estabilidad de la Varianza (Heterocedasticidad)
Se audita si la volatilidad de la demanda ha cambiado históricamente (ej. Pre vs Post Pandemia).
*   **Toma de Decisión:** Si el Coeficiente de Variación se mantiene estable, se evita el uso de transformaciones Log/Box-Cox que podrían dificultar la interpretabilidad del modelo final.

---

## 4. ⚙️ Metodología de Validación de Hipótesis
Cada supuesto de negocio (Festivos, Clima, Quincenas) se valida mediante:
1.  Comparativa de Medias/Medianas.
2.  Visualización de Distribuciones (Boxplots).
3.  Contraste en Reportes JSON para auditoría humana automática.

---

## 5. 📂 Artefactos y Trazabilidad (Dual Persistence)
*   **Knowledge Base:** [phase_03_eda_latest.json](file:///c:/Users/USUARIO/Documents/Forecaster/Tu_Bunuelito/outputs/reports/phase_03/phase_03_eda_latest.json)
*   **Visual Gallery:** 12 gráficas oficiales que documentan cada hallazgo.

---
> [!TIP]
> **Blueprint Lesson:** El análisis de interacciones y retardos es lo que separa un modelo genérico de uno de alta precisión. Entender el *cuándo* y el *con qué* es la llave de la Phase 04.
