import yaml
import os

def load_config(config_path="config.yaml"):
    """
    Carga la configuración desde un archivo YAML.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found at {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config
