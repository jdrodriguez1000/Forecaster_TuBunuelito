import os
import json
from datetime import datetime

def save_report(data, phase_name, outputs_path="outputs/reports"):
    """
    Implementa el Protocolo de Dual Persistencia para reportes JSON.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Versión Histórica
    history_dir = os.path.join(outputs_path, "history")
    os.makedirs(history_dir, exist_ok=True)
    history_path = os.path.join(history_dir, f"{phase_name}_{timestamp}.json")
    
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    
    # Versión Latest (Puntero)
    latest_path = os.path.join(outputs_path, f"{phase_name}_latest.json")
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    
    print(f"Report saved to {latest_path} and {history_path}")

def setup_logging():
    """
    Configura el sistema de logging.
    """
    # Placeholder for logging setup
    pass
