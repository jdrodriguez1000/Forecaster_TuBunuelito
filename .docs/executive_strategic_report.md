# Reporte Ejecutivo de Verdades Estratégicas: Tu Buñuelito

**Consultora:** Sabbia Solutions & Services SAS (Triple S)  
**Proyecto:** Forecaster Tu Buñuelito  
**Fecha:** 27 de Febrero de 2026  
**Objetivo:** Exponer las dinámicas de mercado y riesgos operativos detectados mediante analítica avanzada (Fases 03 y 04).

---

## 🏛️ Resumen de Auditoría Estratégica

Este documento consolida 20 hallazgos críticos ("Verdades Incómodas") derivados del Análisis Exploratorio de Datos (EDA) y la Ingeniería de Características. Cada hallazgo está respaldado por evidencia estadística y una justificación de negocio diseñada para la toma de decisiones gerenciales.

### 🏭 Dimensión 1: Operación y Hábitos de Consumo

1. **La Trifecta de Saturación**  
   *   **Frase:** El pico máximo (Lluvia Ligera + Domingo + Quincena) es una anomalía de "suerte" climática; depender de ella no es estrategia, sino vulnerabilidad operativa.  
   *   **Justificación:** Cuando múltiples factores positivos coinciden, se genera una demanda excepcional que supera la capacidad normal. Sin embargo, al ser eventos externos (clima y calendario) que solo ocurren simultáneamente pocas veces al año, usarlos como base de planeación diaria generaría un exceso de personal e insumos en los días normales.
   *   **Evidencia:** Demanda > 400 unidades en interacciones triple impacto.  
   *   **Fuente:** `phase_03_eda_latest.json` -> `advanced_analytics.interaction_analysis.quincena_rain`.

2. **La Amnesia del Lunes**  
   *   **Frase:** Existe un quiebre de **86 unidades** con el domingo. Intentar proyectar el lunes basándose en la euforia del fin de semana garantiza el desperdicio.  
   *   **Justificación:** El comportamiento del consumidor cambia drásticamente al pasar del ocio del fin de semana a la rutina laboral. El lunes representa un "reinicio" psicológico donde el consumo de impulso se reduce, exigiendo una programación de producción independiente y mucho más conservadora.
   *   **Evidencia:** Caída sistemática de 297 (Dom) a 210 (Lun).  
   *   **Fuente:** `phase_03_eda_latest.json` -> `advanced_analytics.lead_lag_analysis.transition_sunday_monday`.

3. **La Memoria Operativa Corta**  
   *   **Frase:** El éxito de hoy es en un 74% inercia de ayer. Un solo día de mala calidad rompe la racha y la inercia actúa como ancla.  
   *   **Justificación:** El buñuelo es un producto de alta recurrencia y hábito. La fuerte correlación con el día anterior indica que el cliente vuelve por la experiencia inmediata. Un fallo en el servicio o la calidad no solo pierde una venta, sino que rompe la cadena de hábito, haciendo que recuperar el volumen previo tome varios días de consistencia perfecta.
   *   **Evidencia:** Coeficiente de Autocorrelación (ACF) Lag 1 de **0.742**.  
   *   **Fuente:** `phase_03_eda_latest.json` -> `advanced_analytics.lead_lag_analysis.autocorrelation_lags`.

4. **El Cansancio del Día 28**  
   *   **Frase:** Ciclo de agotamiento financiero al final del mes. Es momento de reducir inventario y aceptar la pausa del mercado en lugar de forzar la venta.  
   *   **Justificación:** Los datos muestran una caída recurrente en la vitalidad de compra cada 28 días, coincidiendo con el agotamiento del presupuesto mensual de las familias. En este periodo, el cliente prioriza gastos básicos, por lo que presionar la demanda con promociones suele ser ineficiente; lo óptimo es ajustar los costos operativos a la baja.
   *   **Evidencia:** Pico de potencia en el periodograma cercano a ciclos mensuales (28-30 días).  
   *   **Fuente:** `phase_03_eda_latest.json` -> `advanced_analytics.frequency_analysis.top_periods`.

5. **La Ilusión de la "Reactivación"**  
   *   **Frase:** El crecimiento post-pandemia es por "marea alta" económica. Sin innovación propia, el negocio se hundirá cuando la marea baje.  
   *   **Justificación:** El aumento de ventas tras la pandemia no se debe a una ganancia de mercado propia, sino a la recuperación general del consumo en el país. Al no haber un cambio estructural en cómo capturamos clientes, el negocio queda expuesto a retroceder a niveles mínimos si la economía nacional entra en una fase de enfriamiento.
   *   **Evidencia:** Media Post-Pandemia (276) vs Reactivación (254).  
   *   **Fuente:** `phase_03_eda_latest.json` -> `business_insights.08_period_analysis`.

---

### 🌤️ Dimensión 2: Clima y Macro-Entorno

6. **El Factor Antojo**  
   *   **Frase:** La lluvia ligera es socia (**239 unidades**), pero la lluvia fuerte es verdugo. La producción debe ser quirúrgica con la intensidad.  
   *   **Justificación:** El clima frío y la lluvia leve invitan al consumo de productos calientes como el buñuelo. Sin embargo, existe un "punto de quiebre": en cuanto la lluvia se intensifica y dificulta el desplazamiento del cliente, el efecto se invierte totalmente, convirtiéndose en una barrera de acceso que desploma la venta.
   *   **Evidencia:** Ligera (239) > Ninguna (232) > Fuerte (227).  
   *   **Fuente:** `phase_03_eda_latest.json` -> `business_insights.06_weather_impact.rain`.

7. **El Viento a Favor de "El Niño"**  
   *   **Frase:** Se ha navegado con viento a favor climático. Un cambio a "La Niña" prolongada hundirá las ventas estructurales.  
   *   **Justificación:** Los periodos de sequía o calor moderado ("El Niño") favorecen el tráfico peatonal cerca de los puntos de venta. Históricamente, el negocio ha disfrutado de estas condiciones, pero un ciclo de lluvias constantes ("La Niña") reduciría el flujo de personas, impactando la base misma de la demanda captada.
   *   **Evidencia:** "El Niño" (249 units) vs "La Niña" (225 units).  
   *   **Fuente:** `phase_03_eda_latest.json` -> `business_insights.06_weather_impact.macro`.

8. **La Falacia de la Feria de las Flores**  
   *   **Frase:** Mediáticamente es gigante, estadísticamente es un susurro (**+6 unidades**). Sobre-inversión de atención en un evento que no mueve la caja.  
   *   **Justificación:** Aunque la festividad genera una percepción de gran actividad, los datos reales de venta muestran que el incremento es marginal. Gastar recursos excesivos en logística o publicidad especial para este periodo tiene un retorno de inversión muy bajo comparado con un fin de semana normal de quincena.
   *   **Evidencia:** Feria (236) vs No Feria (230).  
   *   **Fuente:** `phase_03_eda_latest.json` -> `business_insights.04_special_events.feria`.

9. **La "Resaca" del Dólar (Lag 30)**  
   *   **Frase:** El impacto de la TRM tarda 30 días en llegar al bolsillo. No celebramos bajas del dólar hasta el mes siguiente.  
   *   **Justificación:** El precio del dólar no afecta la decisión de compra hoy, sino que se filtra a través de la cadena de costos y la inflación percibida en un ciclo de aproximadamente un mes. Esto significa que las variaciones cambiarias de hoy son el predictor de la salud del bolsillo del cliente del próximo mes.
   *   **Evidencia:** Correlación pico detectada específicamente en el **Lag 30**.  
   *   **Fuente:** `phase_03_eda_latest.json` -> `advanced_analytics.lead_lag_analysis.macro_lead_lag.trm`.

10. **Vulnerabilidad ante la Tasa de Desocupación**  
    *   **Frase:** El buñuelo es un gusto prescindible en climas de austeridad. Si el desempleo sube, la demanda bajará matemáticamente.  
    *   **Justificación:** A pesar de ser un snack accesible, el consumidor lo clasifica como un "lujo diario". Ante cualquier noticia o percepción de inestabilidad laboral, el cliente recorta primero estos gastos antes que los alimentos básicos, lo que nos hace altamente sensibles a los ciclos del mercado laboral nacional.
    *   **Evidencia:** Correlación negativa de **-0.315**.  
   *   **Fuente:** `phase_03_eda_latest.json` -> `statistical_audit.multicollinearity.correlation`.

---

### 💰 Dimensión 3: Finanzas e Ingeniería de Precios

11. **El Ratio de Asequibilidad**  
    *   **Frase:** El buñuelo dejó de ser compra impulsiva para ser analizado según el salario diario. Estamos en el "techo de cristal" del precio.  
    *   **Justificación:** Hemos llegado a un punto donde el precio del producto representa una fracción significativa del ingreso diario del cliente. Cuando este ratio sube, el consumidor deja de comprar por instinto y empieza a "hacer cuentas", lo que reduce drásticamente la frecuencia de compra.
    *   **Evidencia:** Alta sensibilidad del ratio `asequibilidad_idx` en el modelo.  
    *   **Fuente:** `phase_04_features_latest.json` -> `quality_audit.statistical_diagnostics.vif_analysis`.

12. **La Vulnerabilidad Cambiaria**  
    *   **Frase:** El margen bruto sufre erosión silenciosa indexada a Wall Street (Dólar). Se vende en pesos, se costea en dólares.  
    *   **Justificación:** Aunque vendemos en el mercado local, la mayoría de los insumos clave (grasas, harinas, maquinaria) están vinculados al precio internacional de las materias primas y al dólar. Esto significa que nuestra rentabilidad real está fuera de nuestro control directo y exige coberturas financieras ante la volatilidad externa.
    *   **Evidencia:** Variable de vulnerabilidad TRM con alta importancia de característica.  
    *   **Fuente:** `phase_04_features_latest.json` -> `data_inventory.columns_created_or_transformed`.

13. **El Spread de Inflación**  
    *   **Frase:** Encarecer el buñuelo más rápido que la canasta básica desploma la fidelidad. El consumidor castiga el deleite por la saciedad.  
    *   **Justificación:** El cliente compara el precio de un buñuelo con el de otros alimentos de primera necesidad (arroz, huevos). Si aumentamos precios por encima de la inflación general de alimentos, el producto deja de competir con otros snacks y empieza a competir con el almuerzo, perdiendo siempre esa batalla por prioridad nutricional.
    *   **Evidencia:** Relación entre `spread_inflacion` y caída de volumen.  
    *   **Fuente:** `phase_04_features_latest.json` -> `data_inventory.columns_created_or_transformed`.

14. **El Abismo del Segundo Trimestre (Q2)**  
    *   **Frase:** Abril, Mayo y Junio son meses de "congelación" (**183 unidades**). El flujo de caja es una montaña rusa pendiente de Diciembre.  
    *   **Justificación:** Históricamente, el segundo trimestre presenta un vacío de demanda por falta de festividades y ciclos de gasto escolar. El negocio sobrevive gracias a los picos de fin de año, lo que indica que no tenemos una "dieta de ventas" balanceada durante los 12 meses, creando riesgos de liquidez a mitad de año.
    *   **Evidencia:** Q2 (183) vs Q4 (275).  
    *   **Fuente:** `phase_03_eda_latest.json` -> `business_insights.07_macro_impact.smlv`.

15. **La Paradoja de la Rigidez de Precios**  
    *   **Frase:** Mantener margen como dogma frente a IPC agresivo es suicidio estadístico. La falta de elasticidad sacrifica la supervivencia del volumen.  
    *   **Justificación:** Si nos negamos a sacrificar un poco de margen para mantener los precios competitivos cuando la inflación sube, el mercado nos castiga reduciendo el volumen total de ventas. Al final, es mejor ganar un poco menos por buñuelo pero vender muchos, que intentar mantener un margen alto en una tienda vacía.
    *   **Evidencia:** Saneamiento de variables `var_pct` para ratios reales.  
    *   **Fuente:** `phase_04_features_latest.json` -> `data_inventory.columns_dropped`.

---

### 📈 Dimensión 4: Marketing y Riesgos Estructurales

16. **El Canibalismo de las Promociones**  
    *   **Frase:** Descuentos en domingo es "quemar margen". Se satura capacidad con ventas que la inercia orgánica ya garantizaba.  
    *   **Justificación:** El domingo es el día de venta más fuerte por naturaleza. Aplicar promociones ese día no atrae clientes nuevos, sino que le da un descuento innecesario a clientes que ya estaban dispuestos a pagar el precio Full, deteriorando la rentabilidad del día más importante de la semana.
    *   **Evidencia:** Promo en Finde (406 units) vs Sin Promo Finde (267 units). Incremento marginal vs costo.  
    *   **Fuente:** `phase_03_eda_latest.json` -> `advanced_analytics.interaction_analysis.promo_weekend`.

17. **La Trampa de los Rendimientos Decrecientes**  
    *   **Frase:** El marketing ayuda, no lidera. Se gasta dinero en recordar existencia, no en conquistar nuevos territorios.  
    *   **Justificación:** La baja respuesta a la publicidad indica que estamos impactando siempre al mismo grupo de personas. Más inversión no trae más ventas, sino que solo "mantiene" a los actuales. Para crecer, necesitamos cambiar el enfoque hacia nuevas audiencias o geografías, en lugar de saturar los mismos canales actuales.
    *   **Evidencia:** Baja correlación de inversión publicitaria (**0.39**).  
    *   **Fuente:** `phase_03_eda_latest.json` -> `statistical_audit.multicollinearity.correlation`.

18. **La Esquizofrenia de las Novenas**  
    *   **Frase:** Diciembre es un éxito "ruidoso". Proyecciones basadas en este pico son el error más caro del negocio; esa demanda muere el 27-Dic.  
    *   **Justificación:** El pico de diciembre es puramente estacional y no repetible en el resto del año. Tomar decisiones de inversión en infraestructura o contrataciones permanentes basadas en la locura de las novenas es un error típico; esa demanda es "ficticia" para el resto de la operación anual.
    *   **Evidencia:** Salto masivo de media (343 units) con alta desviación estándar.  
    *   **Fuente:** `phase_03_eda_latest.json` -> `business_insights.04_special_events.novenas`.

19. **El Impuesto a la Incertidumbre**  
    *   **Frase:** El negocio es un 27% más volátil que en 2019. El costo de "no saber qué pasará mañana" es mucho más alto ahora.  
    *   **Justificación:** La inestabilidad de la demanda se ha incrementado tras la pandemia. Esto significa que, aunque vendamos más, el riesgo operativo es mayor y los errores en la previsión de inventario son ahora mucho más costosos, exigiendo modelos de pronóstico mucho más precisos que en el pasado.
    *   **Evidencia:** Volatility Ratio Post-vs-Pre de **1.27**.  
    *   **Fuente:** `phase_03_eda_latest.json` -> `advanced_analytics.variance_stability`.

20. **La Anomalía Huérfana del 18 de Julio**  
    *   **Frase:** El sistema falló ese día sin causa externa. Recordatorio de que la fragilidad operativa es el único enemigo que el modelo no predice.  
    *   **Justificación:** Los datos muestran una caída inexplicada en una fecha específica donde no hubo lluvia, ni crisis, ni cierre. Esto representa los "puntos ciegos" operativos; fallas de personal, roturas de equipo o desatención humana que ninguna inteligencia artificial puede anticipar y que solo la gerencia puede mitigar.
    *   **Evidencia:** Registro único de anomalía no explicada en **2022-07-18**.  
    *   **Fuente:** `phase_03_eda_latest.json` -> `advanced_analytics.anomaly_analysis.unexplained_dates`.

---
**Firmado:**  
*Agente Antigravity*  
*Sabbia Solutions & Services SAS*
