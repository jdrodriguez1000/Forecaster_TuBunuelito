# Blueprint: Fase 05 - Modelado (Modeling)

Este documento define la estrategia de configuración de modelos, entrenamiento y validación cruzada. En esta fase se aprovechan las capacidades de `skforecast` para gestionar la dinámica temporal de la serie.

---

## 1. ⚙️ Configuración del Forecaster (skforecast)

La responsabilidad de la dinámica temporal (autorregresión) recae en esta fase para garantizar la integridad de los datos y facilitar el proceso de predicción recursiva/directa.

### **A. Lags y Ventanas Móviles (Autorregresión)**
Delegaremos a `skforecast` la creación de:
*   **Lags Deterministas**: `[1, 7, 14]` (Día anterior, misma semana pasada, hace dos semanas).
*   **Window Features**: `rolling_mean_7` (Promedio móvil de la última semana) para suavizar la señal de entrada al modelo.

### **B. Estrategia de Predicción**
*   **Modelo**: `ForecasterDirect`.
*   **Horizonte**: 185 días.
*   **Razón**: Dado que tenemos variables exógenas potentes, el pronóstico directo evita la acumulación de errores de la estrategia recursiva.

---

## 2. 🧪 Estrategia de Validación y Backtesting

*   **Método**: Validación Cruzada Temporal (Time Series Backtesting).
*   **Métrica Primaria**: MAPE (Mean Absolute Percentage Error).
*   **Meta**: < 12%.
*   **Scoring Adicional**: MAE (para entender el error en unidades de buñuelos) y RMSE (para penalizar grandes desviaciones en días pico).

---

## 3. 🤖 Batería de Modelos Autorizados

Se realizará una competencia de modelos utilizando la semilla global `random_state=42`:
1.  `Ridge`: Modelo base lineal con regularización.
2.  `RandomForestRegressor`: Para capturar interacciones no lineales.
3.  `LGBMRegressor` / `XGBRegressor`: Modelos de Boosting de alta eficiencia.
4.  `HistGradientBoostingRegressor`: Robustez natural ante posibles nulos remanentes.

---

## 4. 📈 Hiperparametrización y Optimización

*   Se utilizará `BayesianSearch` o `GridSearch` sobre los parámetros críticos de cada algoritmo.
*   La búsqueda se centrará en controlar el sobreajuste (*overfitting*), especialmente en los modelos de Boosting debido al tamaño del dataset histórico.

---
**Nota**: Este documento será actualizado con detalles específicos de cuadrículas de parámetros una vez iniciada la Fase 05.
