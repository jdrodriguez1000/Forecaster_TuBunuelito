import pytest
import datetime
import os
from src.utils.helpers import save_report
from src.utils.config_loader import load_config

# Global variable to store results
test_results = {
    "phase": "unit_tests",
    "timestamp": "",
    "description": "Reporte de ejecución de pruebas",
    "components": [], # List of components (files) tested
    "metrics": {
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "total": 0
    },
    "details": []
}

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # Execute all other hooks to obtain the report object
    outcome = yield
    rep = outcome.get_result()

    # We only look at the 'call' phase (the actual test execution)
    if rep.when == "call":
        test_results["metrics"]["total"] += 1
        
        status = "passed" if rep.passed else "failed"
        if rep.skipped:
            status = "skipped"
        
        test_results["metrics"][status] += 1
        
        # Extract component name from file name (test_db_connector.py -> db_connector)
        file_name = os.path.basename(item.fspath)
        component = file_name.replace("test_", "").replace(".py", "")
        
        if component not in test_results["components"]:
            test_results["components"].append(component)
        
        test_results["details"].append({
            "test_name": item.name,
            "component": component,
            "status": status,
            "duration": round(rep.duration, 4),
            "error_message": str(rep.longrepr) if rep.failed else None
        })

def pytest_sessionfinish(session, exitstatus):
    """
    Called after all tests have been executed.
    Saves the accumulated results to a JSON report.
    """
    config = load_config()
    reports_path = config.get("general", {}).get("tests_reports_path", "tests/reports")
    
    test_results["timestamp"] = datetime.datetime.now().isoformat()
    
    # Identify phase name for the report file
    phase_name = "unit_tests"
    
    # Simple logic to detect if we are running integration tests
    # Using the first item's path to decide
    if session.items and "integration" in str(session.items[0].fspath):
        phase_name = "integration_tests"
        test_results["phase"] = "integration_tests"
        test_results["description"] = "Reporte de ejecución de pruebas de integración"
    else:
        test_results["phase"] = "unit_tests"
        test_results["description"] = f"Reporte de ejecución de pruebas unitarias para: {', '.join(test_results['components'])}"

    save_report(test_results, phase_name, outputs_path=reports_path)
