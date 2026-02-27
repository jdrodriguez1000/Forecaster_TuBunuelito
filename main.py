import argparse
import logging
from src.utils.config_loader import load_config
from src.loader import DataLoader
from src.preprocessor import DataPreprocessor
from src.analyzer import DataAnalyzer

# Configuración de logging para producción
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # 1. Cargar configuración inicial
    config = load_config()
    default_mode = config.get("general", {}).get("mode", "load")

    # 2. Configurar argumentos de consola (sobresalen sobre el config.yaml)
    parser = argparse.ArgumentParser(description="Tu Buñuelito Forecasting Pipeline")
    parser.add_argument(
        "--mode", 
        type=str, 
        default=default_mode,
        choices=["load", "train", "forecast"],
        help=f"Modo de ejecución (por defecto en config: {default_mode})"
    )
    args = parser.parse_args()
    
    mode = args.mode
    logger.info(f"--- Iniciando Pipeline en MODO: {mode.upper()} ---")

    try:
        # FASE 01: Extractions (Siempre se ejecuta en 'load' y 'train')
        if mode in ["load", "train"]:
            logger.info("Fase 01: Iniciando Extracción y Auditoría de Datos (Discovery)...")
            loader = DataLoader()
            loader.run_extraction()
            logger.info("Fase 01 completada exitosamente.")

        # Lógica para Fases Futuras
        if mode == "train":
            logger.info("Iniciando Pipeline de Entrenamiento Completo...")
            
            # FASE 02: Preprocessing
            logger.info("Fase 02: Iniciando Limpieza de Integridad y Reindexación...")
            preprocessor = DataPreprocessor()
            preprocessor.run()
            logger.info("Fase 02 completada exitosamente.")
            
            # FASE 03: EDA (Análisis Exploratorio de Datos)
            logger.info("Fase 03: Iniciando Análisis de Estacionariedad, ACF/PACF y Validación de Hipótesis...")
            analyzer = DataAnalyzer()
            analyzer.run()
            logger.info("Fase 03 completada exitosamente.")
            
            # Aquí se llamarán: Features -> Modeling
            logger.warning("Fases posteriores a 'EDA' aún no implementadas.")
            
        elif mode == "forecast":
            logger.info("Iniciando Pipeline de Inferencia (Forecast)...")
            # Aquí se llamarán: Load (incremental) -> Features -> Predict
            logger.warning("Modo 'forecast' aún no implementado.")

        if mode == "load":
            logger.info("Modo 'load' finalizado. Revisa el reporte de auditoría antes de continuar.")

    except Exception as e:
        logger.error(f"Error crítico en la ejecución del pipeline: {str(e)}", exc_info=True)
        exit(1)

if __name__ == "__main__":
    main()
