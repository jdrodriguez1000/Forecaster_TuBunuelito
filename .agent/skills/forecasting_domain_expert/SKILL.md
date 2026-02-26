---
name: forecasting_domain_expert
description: Encapsula el conocimiento experto sobre las dinámicas de venta, estacionalidad y proyecciones matemáticas específicas para el negocio de buñuelos de Tu Buñuelito.
---

# Skill: Experto en el Dominio de Pronóstico (Tu Buñuelito)

Esta habilidad dota al agente del conocimiento experto sobre el comportamiento del consumidor, ciclos logísticos y factores externos que afectan la demanda del producto estrella de **Tu Buñuelito** (Cafetería SAS).

## 1. 🏢 Contexto Estratégico y Objetivo
*   **Producto Estrella:** El Buñuelo.
*   **Variable Objetivo:** `demanda_teorica_total` (Calculada como: `ventas_reales_totales` + `unidades_agotadas`).
*   **Horizonte Técnico:** 185 días (Proyección diaria continua).
*   **Regla de Oro (Anti-Leakage):** El modelo solo utiliza información disponible hasta las 23:59 del día anterior ($T-1$).

## 2. 📅 Calendario de Negocio (Business Features)

### A. Estacionalidad Mensual y Especial
*   **Pico Máximo:** Diciembre (Novenas y Navidad).
*   **Temporada Alta:** Enero, Junio y Julio (Vacaciones y temporada media).
*   **Eventos de Impacto "Domingo":** Las ventas suben a niveles de domingo en:
    *   **Novenas Navideñas:** 16 al 26 de diciembre.
    *   **Semana Santa:** Jueves y Viernes Santo.
    *   **Feria de las Flores:** 1 al 10 de agosto.

### B. Ciclos de Flujo de Caja (Patrones de Pago)
*   **Quincenas:** Incremento de demanda los días 15-16 y 30-31 de cada mes.
*   **Primas Legales:** Incrementos significativos del **15 al 20 de Junio** y del **15 al 20 de Diciembre**.
*   **Días de la Semana:** Domingo (Máximo), Sábado y Viernes.
*   **Festivos:** Deben tratarse estadísticamente con el peso de un **Sábado**.

### C. Estrategia Promocional y Marketing
*   **Promoción 2x1:** Activa desde 2022 en dos ciclos:
    *   **Ciclo 1:** 01 de abril al 31 de mayo.
    *   **Ciclo 2:** 01 de septiembre al 31 de octubre.
*   **Marketing (Ads):** La pauta en IG/FB se activa **20 días antes** de la promoción y se apaga el **día 25 del mes final** de la promoción.

## 3. 🌤️ Factor Climático (Impacto Variable)
La demanda tiene una sensibilidad probada al clima:
*   **Lluvia Ligera:** Estimula la venta (correlación positiva).
*   **Lluvia Fuerte:** Desestimula la venta por caída de tráfico (correlación negativa).

## 4. 📈 Proyección de Variables Exógenas (Horizonte 185 días)
Para alimentar el `ForecasterDirect` en el futuro, se aplican las siguientes heurísticas:
*   **Macroeconómicas (`trm`, `ipc`, `desempleo`, `smlv`):** Mantener el último valor conocido (**Forward Fill**) o aplicar promedios móviles si hay tendencia clara.
*   **Clima:** Usar promedios históricos del mes o asumir "Día Normal" (Moda histórica).
*   **Calendario/Promos:** Proyectarse de forma determinista según las reglas de fechas fijas.

## 5. 🛠️ Protocolo de Imputación y Limpieza (Data Truth)

### A. Continuidad Temporal
*   **Regla:** Si falta una fecha en la serie, se inserta con valores `NaN`.
*   **Imputación en Preprocesamiento:**
    *   **Ventas:** Los huecos en ventas se imputan con **0**.
    *   **Macro/Clima:** Se usa `Forward Fill` (propagar último valor) y `Back Fill` solo para el inicio de la serie.

### B. Reconstrucción de la Demanda (Variable Objetivo)
*   **Fórmula Obligatoria:** `demanda_teorica_total` = `ventas_reales_totales` + `unidades_agotadas`. 
*   *Nota: Es vital sumar los agotados para capturar la demanda potencial que el inventario no pudo satisfacer.*

### C. Consistencia de Promociones (`es_promocion`)
*   Se debe validar y forzar a `1` si la fecha cae en las ventanas de Abr-May o Sep-Oct (post-2022).
*   Cualquier nulo fuera de estas ventanas o fechas pre-2022 se fuerza a `0`.

## 6. ⚠️ Diferenciación entre Materia Prima y Producto Terminado
*   **Kit (Materia Prima):** Inventario acumulable (bodega). No afecta directamente la demanda diaria si hay stock.
*   **Buñuelo (Producto Terminado):** Vida útil de **1 día**. Cualquier nulo en desecho o inventario final de día se trata como pérdida total.
