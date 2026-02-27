import unittest
import json
import os
import sys
from datetime import datetime

# Añadir el directorio raíz al path para que encuentre 'src'
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

def run_all_unit_tests():
    """Ejecuta todas las pruebas unitarias y genera un reporte JSON de calidad."""
    loader = unittest.TestLoader()
    start_dir = 'tests/unit'
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Crear carpeta de reportes si no existe
    report_dir = 'tests/reports'
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)
    
    # Ejecutar pruebas
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Consolidar resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_data = {
        "phase": "unit_testing",
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_tests": result.testsRun,
            "successful": result.testsRun - len(result.failures) - len(result.errors),
            "failures": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped)
        },
        "details": {
            "failures": [str(f[0]) for f in result.failures],
            "errors": [str(e[0]) for e in result.errors]
        },
        "status": "PASS" if result.wasSuccessful() else "FAIL"
    }
    
    # Dual Persistencia (Latest + History)
    latest_path = os.path.join(report_dir, "unit_tests_report_latest.json")
    history_path = os.path.join(report_dir, f"history/unit_tests_report_{timestamp}.json")
    
    if not os.path.exists(os.path.dirname(history_path)):
        os.makedirs(os.path.dirname(history_path))
        
    with open(latest_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=4)
        
    with open(history_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=4)
        
    print(f"\n✅ Reporte de pruebas generado en: {latest_path}")
    return report_data["status"]

if __name__ == "__main__":
    status = run_all_unit_tests()
    if status == "FAIL":
        sys.exit(1)
    sys.exit(0)
