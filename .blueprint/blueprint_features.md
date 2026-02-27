# Blueprint: Fase 04 - Ingeniería de Características (Feature Engineering)

Este documento detalla la estrategia técnica y de negocio para la transformación de datos y creación de variables en el proyecto "Tu Buñuelito". El objetivo es pasar de datos crudos limpios a un set de entrenamiento de alta potencia predictiva (MAPE objetivo < 12%) y capacidad de simulación estratégica.

El resultado de esta fase se consolidará en un archivo **.parquet** ubicado en **`data/04_processed/`**, el cual servirá como el insumo definitivo para el entrenamiento y la inferencia.

---

## 🏗️ Crónica de Refinamiento y Saneamiento (Bitácora de VIF)

Fiel a la metodología de "Búsqueda de la Señal Pura", esta fase no fue lineal, sino un proceso iterativo de auditoría estadística para eliminar la redundancia y el ruido.

### **Paso 1: Construcción Inicial (Feature Discovery)**
*   Se crearon variables de calendario (mes, día, fin de semana).
*   Se implementaron los ratios de negocio (Asequibilidad, Spread de Inflación, Intensidad de Pauta).
*   Se incluyeron términos de **Fourier** para estacionalidad y flags de proximidad (is_pre_monday).
*   **Diagnóstico VIF 1**: Se detectó una multicolinealidad masiva (VIF > 10,000) en variables como `ads_activos`, `campaña_activa`, `smlv`, `trm`, e inflaciones nominales.
*   **Acción**: Se decidió eliminar las "Variables Padre" y mantener solo los **Ratios**. Se eliminó Fourier por causar inestabilidad numérica.

### **Paso 2: Saneamiento de Multicolinealidad e Integridad (VIF 2)**
*   Se eliminaron variables redundantes como `is_pre_monday`.
*   Se identificó un problema de **Missing Values (NaNs)** en el cálculo del `ipc_momentum` (primeros 90 días).
*   **Acción**: Se implementó un `dropna()` final obligatorio para garantizar que el modelo solo entrene con datos 100% reales.
*   **Diagnóstico VIF 2**: VIFs bajaron drásticamente, pero se detectaron señales de **VIF Infinity** en las variaciones porcentuales (`precio_var_pct`, `smlv_var_pct`).

### **Paso 3: Saneamiento Final y Delegación (VIF Final - Estado Actual)**
*   **Eliminación de Variaciones**: Se movieron `precio_var_pct` y `smlv_var_pct` a la lista de descarte (drop), manteniendo sus ratios hijos (`asequibilidad_idx`, `smlv_real_growth`).
*   **Eliminación de `is_weekend`**: Se descartó a favor de **`day_of_week`** para eliminar la correlación de 0.86 detectada entre ambas.
*   **Eliminación de `target_lag_7`**: Se eliminó la creación manual de retardos del target (incluyendo `intensidad_pauta`) para evitar **Data Leakage** y redundancias. Esta responsabilidad se delega 100% a la librería `skforecast`.
*   **Resultado Final**: El dataset alcanzó un estado de salud perfecto con **VIF < 5** en la mayoría de variables y **Cero Correlaciones Altas**.

---

## 1. 🔍 Auditoría de Columnas (Estado Final)

### **A. Variables que CONTINÚAN (Señales Puras)**
| Columna | Uso Predictivo | Justificación |
| :--- | :--- | :--- |
| `fecha` | Eje Temporal | Base para extracción de estacionalidad. |
| `es_promocion` | Driver Directo | Impacto de +110 unidades detectado en EDA. |
| `porcentaje_margen` | Finanzas | Variable atómica clave para simulaciones. |
| `tasa_desempleo` | Macroeconomía | Correlación negativa detectada (-0.31). |
| `temperatura_media` | Clima | Driver continuo de comportamiento térmico. |
| `tipo_lluvia` | Clima | Categoría filtrada (Ligera/Fuerte). |
| `evento_macro` | Ciclos | Fenómenos climáticos de largo plazo. |

### **B. Variables que NO CONTINÚAN (Eliminación por Ruido, VIF o Leakage)**
| Grupo | Variables Eliminadas | Razón Técnica |
| :--- | :--- | :--- |
| **Operativas** | `unidades_*`, `kit_*`, `buñuelos_*` | Redundancia con target o consecuencia de la demanda. |
| **Leakage** | `buñuelos_preparados`, `target_lag_7` | Información no disponible en T-1 o delegada al modelo. |
| **VIF Infinity** | `ads_activos`, `smlv`, `trm`, `ipc`, `var_pct` | Son componentes de ratios. Su presencia duplica información. |
| **Redundancia** | `is_weekend`, `es_dia_lluvioso`, `fourier` | Capturadas por otras señales (day_of_week, rain_types). |

---

## 2. ✨ Ingeniería de Características (Variables Sintéticas)

### **A. Flags de Negocio (Reglas del Charter)**
*   `es_quincena`: Días 15, 16, 30 y 31 (Impacto en liquidez).
*   `es_prima_legal`: Beneficio semestral (Junio/Diciembre).
*   `es_novena`: 16 al 26 de Diciembre (Pico estacional masivo).
*   `es_feria_flores`: 1 al 10 de Agosto (Comportamiento de festivo).
*   `is_sunday`: El día de mayor volumen del proyecto.

### **B. Ratios Estratégicos (Drivers de Simulación)**
*   `asequibilidad_idx`: Precio / (Salario Diario). Mide el esfuerzo de compra.
*   `spread_inflacion`: Diferencial de encarecimiento (Producto vs Economía).
*   `smlv_real_growth`: Crecimiento del salario por encima de la inflación.
*   `vulnerability_trm`: Dependencia del costo de insumos frente al dólar (Lag 30).

### **C. Interacciones de Potencia**
*   `interaction_es_promocion_is_sunday`: Mide la sinergia entre el descuento y el día pico.
*   `interaction_es_quincena_is_heavy_rain`: Mide si tener dinero diluye el efecto negativo de la lluvia.

---

## 3. 🛠️ Protocolo de Calidad e Implementación

*   **Regla de Oro (T-1)**: Todas las transformaciones (Lags de 30 días en TRM, Momentum de IPC) se realizan con datos históricos. No hay uso de información del día $T$ para predecir $T$.
*   **Limpieza de Nulos**: Se exige un dataset sin NaNs. Cualquier registro incompleto por efecto de ventanas móviles es eliminado antes del entrenamiento.
*   **Dual Persistencia**: 
    *   `data/04_processed/dataset_features_latest.parquet` (Puntero).
    *   `outputs/reports/phase_04/phase_04_features_latest.json` (Auditoría VIF/Corr).

---
**Aprobación Final**: El dataset resultante de esta crónica de refinamiento es considerado la **Versión Oro** para el modelado. Presenta independencia estadística total y una alineación perfecta con las reglas del negocio de Tu Buñuelito.
