import nbformat as nbf
import os

def generate_discovery_notebook():
    """
    Genera el notebook de Data Discovery.
    """
    nb = nbf.v4.new_notebook()
    
    nb['cells'] = [
        nbf.v4.new_markdown_cell("# Fase 01: Data Discovery & Audit\nEste notebook realiza la auditoría inicial de los datos."),
        nbf.v4.new_code_cell("from src.utils.config_loader import load_config\nconfig = load_config()\nprint(config)")
    ]
    
    notebook_path = "experiments/phase_01_discovery/discovery_lab.ipynb"
    with open(notebook_path, 'w', encoding='utf-8') as f:
        nbf.write(nb, f)
    
    print(f"Notebook generated at {notebook_path}")

if __name__ == "__main__":
    generate_discovery_notebook()
