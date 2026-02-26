import argparse
from src.utils.config_loader import load_config

def main():
    parser = argparse.ArgumentParser(description="Tu Buñuelito Forecasting Pipeline")
    parser.add_argument("--phase", type=str, required=True, help="Fase a ejecutar (discovery, preprocessing, etc.)")
    args = parser.parse_args()
    
    config = load_config()
    print(f"Executing phase: {args.phase}")
    
    # Lógica de orquestación por fase
    if args.phase == "discovery":
        print("Starting Discovery Phase...")
    elif args.phase == "preprocessing":
        print("Starting Preprocessing Phase...")
    else:
        print(f"Unknown phase: {args.phase}")

if __name__ == "__main__":
    main()
