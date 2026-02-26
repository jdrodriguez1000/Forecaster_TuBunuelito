# Project Charter: Forecasting "Tu Buñuelito"

## 1. Información General del Proyecto

- **Nombre del Proyecto:** Pronóstico de Demanda "Tu Buñuelito"
- **Cliente:** Cafetería SAS
- **Producto Estrella:** El Buñuelo
- **Consultor / Proveedor:** Sabbia Solutions & Services SAS (Triple S)

## 2. Contexto y Justificación (El Problema)

Actualmente, Cafetería SAS realiza el pronóstico de la demanda de su producto estrella, el buñuelo, a través de un comité de expertos conformado por las áreas de producción, ventas y finanzas. Sin embargo, este proceso presenta múltiples deficiencias que impactan directamente en la rentabilidad y operatividad de la empresa:

1. **Problemas de Inventario:** Existe una constante inestabilidad en el stock, presentándose frecuentemente quiebres de inventario (quedarse sin producto) o excesos del mismo.
2. **Alta Desviación:** El error o desfase entre el pronóstico planeado y la demanda real llega a alcanzar hasta un **25%**.
3. **Falta de Criterio Técnico:** A pesar de contar con información diaria del sistema, el equipo agrupa los datos de forma mensual para generar pronósticos sin una metodología clara. Los criterios varían constantemente: en ocasiones se basan en el mes anterior, otras en el mismo mes del año pasado, o simplemente se asigna un número para cumplir con una meta preestablecida. En general, el método es variado y poco confiable.
4. **Sesgo Humano y Manipulación:** El proceso es altamente influenciable por las directivas. Los gerentes comercial, de operaciones, financiero y general terminan acordando o ajustando las cifras para que calcen con las necesidades o deseos de la empresa, alejándose de la realidad basada en datos.

## 3. Objetivo del Proyecto

El objetivo principal de Sabbia Solutions & Services SAS (Triple S) es desarrollar e implementar una **aplicación analítica basada en datos** que permita a Cafetería SAS pronosticar de manera precisa y objetiva la demanda real de buñuelos para un horizonte de **185 días diarios** (garantizando la cobertura del mes actual y los 5 meses siguientes).

Con esta solución se busca:
- Disminuir drásticamente la influencia humana y los sesgos en la generación de pronósticos.
- Proveer a la empresa de una herramienta confiable que apoye la toma de las mejores decisiones operativas y financieras.
- Optimizar la gestión de inventarios (reducción de excesos y faltantes de stock).

## 4. Alcance Inicial

- **Horizonte de Pronóstico:** 185 días fijos a nivel diario (con lógica de visualización de meses completos para el reporte gerencial).
- **Granularidad de los Datos:** Información diaria (actualmente agrupada a nivel mensual por el cliente, pero se analizará la mejor granularidad técnica para el modelo).
- **Entregable Principal:** Aplicación de pronóstico de demanda.

## 5. Reglas de Negocio y Estacionalidad de la Demanda

Con base en la experiencia del cliente, se han identificado patrones de comportamiento importantes en los datos a nivel diario que deben ser capturados por el modelo predictivo:

- **Efecto Día de la Semana:**
  - Los domingos son los días de mayor venta.
  - Le siguen los sábados y los viernes.
- **Efecto Festivos:**
  - Los días festivos presentan un comportamiento de ventas similar a un sábado.
- **Efecto Quincena y Fechas de Pago:**
  - Las ventas aumentan en los días de quincena (15-16 y 30-31 de cada mes).
  - Las ventas aumentan notablemente durante los días de pago de la "Prima Legal" en Colombia (del 15 al 20 de junio y del 15 al 20 de diciembre).
- **Efecto Festividades y Eventos Especiales:**
  - **Novenas Navideñas (16 al 26 de diciembre):** Las ventas suben a niveles equivalentes a los de un domingo.
  - **Semana Santa (Jueves y Viernes Santo):** Las ventas suben a niveles equivalentes a los de un domingo.
  - **Feria de las Flores (1 al 10 de agosto):** Las ventas suben a niveles equivalentes a los de un domingo.
- **Estacionalidad Mensual:**
  - El mes con el mayor volumen de ventas es **Diciembre**.
  - Los siguientes mejores meses son: **Enero, Junio y Julio**.
- **Eventos Anómalos (Pandemia):**
  - Se registró una caída significativa en las ventas durante la pandemia, específicamente entre el **1 de mayo de 2020 y el 30 de abril de 2021**.
  - A partir de mayo 2021 inició un periodo de recuperación.
  - Desde el año **2023 en adelante**, el volumen de ventas se estabilizó volviendo a niveles aceptables y normales.
- **Efecto del Clima:**
  - Lluvia ligera: Correlación positiva (se vende más).
  - Lluvia fuerte: Correlación negativa (se vende menos).
- **Variables Macroeconómicas:**
  - El cliente sospecha que factores como el alza del salario mínimo, la Tasa Representativa del Mercado (TRM), el Índice de Precios al Consumidor (IPC) y la tasa de desempleo podrían afectar la demanda, aunque no tiene evidencia estadística actual. Se evaluará la viabilidad de incorporar estas variables en el modelo.
- **Promociones y Marketing:**
  - **Promoción 2x1:** Vigente desde el año 2022, se realiza en dos momentos del año:
    - Periodo 1: del 1 de abril al 31 de mayo.
    - Periodo 2: del 1 de septiembre al 31 de octubre.
  - **Campañas en Redes Sociales (Facebook e Instagram):**
    - La inversión (pauta) se activa aproximadamente **20 días antes** del inicio de cada promoción.
    - La pauta publicitaria se apaga el **día 25 del mes en el que finaliza** la promoción correspondiente (ej. 25 de mayo y 25 de octubre).

## 6. Gestión de Inventarios y Pedidos

La dinámica de abastecimiento y ventas tiene particularidades operativas muy importantes que deberán considerarse, ya que impactan directamente el objetivo de la predicción y el cálculo de la demanda:

- **Materia Prima (El "Kit"):**
  - Un (1) Kit (que incluye harina, queso, huevos, etc.) rinde para preparar **50 buñuelos**.
  - El stock de este kit se acumula en bodega de forma normal (no perece de forma diaria).
  - La logística se divide en dos ciclos fijos mensuales:
    - **Ciclo 1:** Se pide el día 15 de cada mes. Se entrega el último día del mes y debe cubrir la operación hasta el día 14 del mes siguiente.
    - **Ciclo 2:** Se pide el día 1 de cada mes. Se entrega el día 14 y debe cubrir la operación hasta el final del mes.
- **Producto Terminado (El Buñuelo Preparado):**
  - Posee una vida útil de **un (1) solo día**.
  - **Preparación:** La cantidad a fritar cada día es una decisión del dueño, basada en su propia expectativa matemática (la cual buscamos optimizar).
  - **Ventas Reales:** Están limitadas no solo por la cantidad de clientes, sino por el inventario disponible. Se define como el *mínimo* entre los buñuelos preparados y la demanda total real de ese día.
  - **Desperdicios (Merma):** Producto preparado que no se vende al finalizar la jornada. Este producto se considera una pérdida de 100%.
  - **Agotados:** Cuota de demanda no satisfecha porque se terminaron los buñuelos preparados, independientemente de que existiera o no materia prima en bodega en ese momento.

## 7. Origen y Estructura de Datos

Toda la información histórica necesaria para el proyecto se encuentra consolidada en una base de datos en **Supabase**. La data histórica inicia el **2017-01-01** y se actualiza de manera automática **diariamente**, lo que significa que la granularidad temporal es continua hasta la fecha de ejecución. A continuación, se detalla la estructura de las 6 tablas principales dispuestas por el cliente:

### 7.1. Tabla: `ventas`
Contiene la información transaccional diaria.
- **Campos principales:** `fecha`, `unidades_totales`, `unidades_pagas`, `unidades_bonificadas`, `es_promocion`, `ads_activos`.

### 7.2. Tabla: `inventario`
Registra la trazabilidad logística tanto del Kit de materia prima como del producto terminado diario.
- **Campos principales:** 
  - *Materia prima:* `fecha`, `kit_inicial_bodega`, `kit_recibido`, `lbs_recibidas`, `kit_final_bodega`.
  - *Producto terminado y demanda:* `demanda_teorica_total`, `buñuelos_preparados`, `ventas_reales_totales`, `ventas_reales_pagas`, `ventas_reales_bonificadas`, `buñuelos_desperdiciados`, `unidades_agotadas`.

### 7.3. Tabla: `finanzas`
Registra los datos financieros asociados a los costos y márgenes diarios.
- **Campos principales:** `fecha`, `precio_unitario`, `costo_unitario`, `margen_bruto`, `porcentaje_margen`.

### 7.4. Tabla: `marketing`
Registra la traza de la inversión publicitaria en redes sociales.
- **Campos principales:** `fecha`, `inversion_total`, `ig_cost`, `fb_cost`, `ig_pct`, `fb_pct`, `campaña_activa`.

### 7.5. Tabla: `macroeconomia`
Contiene variables macroeconómicas exógenas de interés para el modelo.
- **Campos principales:** `fecha`, `smlv`, `inflacion_mensual_ipc`, `tasa_desempleo`, `trm`.

### 7.6. Tabla: `clima`
Registra variables meteorológicas de la ciudad de operación y factores climáticos globales.
- **Campos principales:** `fecha`, `temperatura_media`, `probabilidad_lluvia`, `precipitacion_mm`, `tipo_lluvia`, `evento_macro` (ej. La Niña, El Niño), `es_dia_lluvioso`.

## 8. Enfoque Metodológico y Tecnológico

Para abordar el problema analítico y generar los pronósticos, se ha definido el siguiente stack tecnológico y diseño del modelo según los lineamientos del equipo técnico:

- **Librería Base:** Se utilizará **`skforecast`**, especializada en la creación de modelos de Machine Learning para series de tiempo.
- **Estrategia de Pronóstico:** Se implementará un enfoque de Pronóstico Directo (**Forecaster Directo**).
- **Modelos Candidatos (Algoritmos):** Se entrenarán y evaluarán inicialmente los siguientes modelos para encontrar el de mejor desempeño:
  - *Ridge*
  - *RandomForest*
  - *LightGBM*
  - *XGBoost*
  - *GradientBoosting*
  - *HistGradientBoosting*
- **Horizonte y Granularidad:** 
  - El modelo ejecutará las predicciones a **nivel diario**, proyectando un horizonte estricto de **185 días**.
  - **Regla de Visualización Mensual (Cierre de Periodos):** Para asegurar una lectura estratégica sin distorsiones por meses a medias, se aplicará el siguiente post-procesamiento en la agrupación mensual:
    - **Mes en Curso (Cierre Híbrido):** El reporte mensual mostrará el mes actual como completo, sumando las *ventas reales* registradas hasta el día de proceso más el *pronóstico* para el resto del mes.
    - **Proyecciones de Meses Futuros:** Solo se graficarán y reportarán aquellos meses futuros que el horizonte de 185 días logre cubrir de **forma íntegra (del día 1 al 30/31)**. 
    - **Exclusión de Meses Incompletos:** Cualquier periodo mensual al final de la serie que no cuente con la totalidad de los días pronosticados será descartado visualmente, evitando inducir al comité a conclusiones erróneas sobre caídas de demanda.
- **Variables Autorregresivas (Lags):** El modelo tomará en consideración el historial propio de la serie de tiempo. Para realizar la predicción, el modelo tendrá muy en cuenta las **ventas reales obtenidas hasta el día inmediatamente anterior** a la fecha de pronóstico.

## 9. Criterios de Éxito

El proyecto se considerará completamente exitoso si cumple con los siguientes parámetros técnicos y de negocio:

1. **Criterio Técnico (Precisión):** El modelo de Machine Learning seleccionado debe superar consistentemente a las metodologías actuales baselínea en todas las métricas de error (MAE, MAPE, RMSE) evaluadas sobre el set de validación y test. Específicamente, se establece como meta técnica lograr un **MAPE (Mean Absolute Percentage Error) inferior al 12%**.
2. **Criterio Operativo (Adopción):** La herramienta desarrollada debe ser adoptada formalmente por el comité de expertos (producción, ventas y finanzas) de Cafetería SAS como su insumo automatizado principal para la toma de decisiones y planeación de inventarios diarios y mensuales, reduciendo la intervención subjetiva.

---
*Nota: Este Project Charter es un documento vivo y será actualizado a medida que se definan aspectos técnicos adicionales tales como fuentes de datos, entregables específicos intermedios y cronograma. Todo entregable técnico (Reportes JSON, Modelos PKL, Gráficas y Pronósticos CSV) seguirá un protocolo de **Dual Persistencia** (Versión Histórica con timestamp en subcarpeta `history/` y Versión Puntero `_latest` en la raíz de su carpeta correspondiente en `outputs/`).*
