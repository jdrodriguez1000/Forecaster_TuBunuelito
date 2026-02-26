import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List
from src.utils.config_loader import load_config

logger = logging.getLogger(__name__)

class DataAuditor:
    """
    Componente especializado en la auditoría de calidad y cumplimiento de contratos de datos.
    Implementa las reglas de 'Abogado del Diablo' para detectar anomalías antes de la fase de preprocesamiento.
    """

    def __init__(self):
        self.config = load_config()
        self.extraction_config = self.config.get("extractions", {})
        self.schemas = self.extraction_config.get("schemas", {})
        self.sentinels = self.extraction_config.get("sentinel_values", {})

    def audit_dataframe(self, df: pd.DataFrame, table_name: str) -> Dict[str, Any]:
        """
        Realiza una auditoría completa de un DataFrame basado en su nombre de tabla y esquema configurado.
        """
        report = {
            "table_name": table_name,
            "shape": {"rows": df.shape[0], "columns": df.shape[1]},
            "contract_validation": self._validate_contract(df, table_name),
            "integrity_checks": self._check_integrity(df),
            "quality_metrics": self._analyze_quality(df),
            "statistical_profile": self._generate_profile(df, table_name),
            "business_rules_validation": self._validate_business_rules(df, table_name)
        }
        return report

    def _validate_business_rules(self, df: pd.DataFrame, table_name: str) -> Dict[str, Any]:
        """
        Valida reglas lógicas y matemáticas específicas del negocio (Tu Buñuelito).
        Detecta inconsistencias en balances de ventas e inventario.
        """
        results = {"violations_count": 0, "details": []}

        # 1. Regla de No Negatividad (Puntos 19 y 20)
        if table_name in ["ventas", "inventario"]:
            schema = self.schemas.get(table_name, {})
            numeric_cols = [col for col, t in schema.items() if t in ["int", "float"]]
            for col in numeric_cols:
                if col in df.columns:
                    neg_count = int((df[col] < 0).sum())
                    if neg_count > 0:
                        results["violations_count"] += 1
                        results["details"].append(f"Columna '{col}': {neg_count} valores negativos detectados.")

        # 2. Reglas específicas de VENTAS
        if table_name == "ventas":
            cols = ["unidades_totales", "unidades_pagas", "unidades_bonificadas", "es_promocion"]
            if all(c in df.columns for c in cols):
                # Punto 15: unidades_pagas == unidades_bonificadas (Solo si es promoción)
                # Punto 17: Relación es_promocion y unidades_bonificadas
                mask_promo = df["es_promocion"] == 1
                mask_no_promo = df["es_promocion"] == 0
                
                # Inconsistencia Punto 15 (asumiendo que aplica en promo 2x1)
                v15 = int((mask_promo & (df["unidades_pagas"] != df["unidades_bonificadas"])).sum())
                if v15 > 0:
                    results["violations_count"] += 1
                    results["details"].append(f"Punto 15: {v15} filas donde pagas != bonificadas en promoción.")

                # Inconsistencia Punto 17 (Bonificadas > 0 iff Promo == 1)
                v17a = int((mask_promo & (df["unidades_bonificadas"] <= 0)).sum())
                v17b = int((mask_no_promo & (df["unidades_bonificadas"] > 0)).sum())
                if v17a + v17b > 0:
                    results["violations_count"] += 1
                    results["details"].append(f"Punto 17: {v17a+v17b} inconsistencias entre 'es_promocion' y 'unidades_bonificadas'.")

                # Punto 16: Totales = Pagas + Bonificadas
                v16 = int((df["unidades_totales"] != (df["unidades_pagas"] + df["unidades_bonificadas"])).sum())
                if v16 > 0:
                    results["violations_count"] += 1
                    results["details"].append(f"Punto 16: {v16} filas donde la suma de unidades no coincide con el total.")

        # 3. Reglas específicas de INVENTARIO
        if table_name == "inventario":
            # Usamos nombres con ñ tal cual están en el contrato
            cols_inv = [
                "ventas_reales_totales", "ventas_reales_pagas", "ventas_reales_bonificadas",
                "buñuelos_preparados", "buñuelos_desperdiciados", "unidades_agotadas", 
                "demanda_teorica_total"
            ]
            if all(c in df.columns for c in cols_inv):
                # Punto 21: ventas_reales_totales = pagas + bonificadas
                v21 = int((df["ventas_reales_totales"] != (df["ventas_reales_pagas"] + df["ventas_reales_bonificadas"])).sum())
                if v21 > 0:
                    results["violations_count"] += 1
                    results["details"].append(f"Punto 21: {v21} inconsistencias en suma de ventas reales.")

                # Punto 22: buñuelos_desperdiciados = preparados - ventas_totales
                v22 = int((df["buñuelos_desperdiciados"] != (df["buñuelos_preparados"] - df["ventas_reales_totales"])).sum())
                if v22 > 0:
                    results["violations_count"] += 1
                    results["details"].append(f"Punto 22: {v22} inconsistencias en cálculo de desperdicio.")

                # Punto 23: unidades_agotadas = demanda_total - preparados
                # Nota: Validamos solo si hay demanda insatisfecha (si preparados < demanda)
                v23 = int((df["unidades_agotadas"] != (df["demanda_teorica_total"] - df["buñuelos_preparados"])).sum())
                if v23 > 0:
                    results["violations_count"] += 1
                    results["details"].append(f"Punto 23: {v23} inconsistencias en cálculo de unidades agotadas.")

        return results

    def _validate_contract(self, df: pd.DataFrame, table_name: str) -> Dict[str, Any]:
        """Validación de columnas esperadas, tipos y presencia de columnas extra."""
        schema = self.schemas.get(table_name, {})
        expected_cols = set(schema.keys())
        actual_cols = set(df.columns)

        missing_cols = list(expected_cols - actual_cols)
        extra_cols = list(actual_cols - expected_cols)
        
        # Validación de tipos básica
        type_mismatches = {}
        for col in expected_cols.intersection(actual_cols):
            expected_type = schema[col]
            actual_dtype = str(df[col].dtype)
            
            # Mapeo simple de validación
            is_valid = True
            if expected_type == "int" and not ("int" in actual_dtype or "uint" in actual_dtype):
                is_valid = False
            elif expected_type == "float" and not ("float" in actual_dtype):
                is_valid = False
            elif expected_type == "datetime" and not ("datetime" in actual_dtype or "object" in actual_dtype):
                is_valid = False # Nota: a menudo se cargan como object inicialmente
            
            if not is_valid:
                type_mismatches[col] = {"expected": expected_type, "actual": actual_dtype}

        return {
            "is_contract_valid": len(missing_cols) == 0 and len(type_mismatches) == 0,
            "missing_columns": missing_cols,
            "extra_columns": extra_cols,
            "type_mismatches": type_mismatches,
            "duplicated_columns": df.columns[df.columns.duplicated()].tolist()
        }

    def _check_integrity(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Chequeo de duplicados y continuidad temporal."""
        checks = {}
        
        # Filas repetidas
        checks["duplicated_rows_count"] = int(df.duplicated().sum())
        
        # Fecha duplicada (pero no fila completa)
        if "fecha" in df.columns:
            # Asegurar que sea datetime para este chequeo
            temp_date = pd.to_datetime(df["fecha"], errors="coerce")
            checks["duplicated_dates_count"] = int(temp_date.duplicated().sum())
            
            # Huecos en fechas (si la serie es diaria)
            if not temp_date.isna().any():
                temp_date = temp_date.sort_values()
                all_dates = pd.date_range(start=temp_date.min(), end=temp_date.max(), freq='D')
                missing_dates = all_dates.difference(temp_date)
                checks["date_gaps_count"] = len(missing_dates)
                checks["date_gaps_sample"] = [d.strftime('%Y-%m-%d') for d in missing_dates[:5]]
            else:
                checks["date_gaps_count"] = "N/A (Existen nulos en fecha)"

        return checks

    def _analyze_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detección de nulos, centinelas, varianza cero y cardinalidad."""
        quality = {
            "null_counts": df.isna().sum().to_dict(),
            "sentinel_counts": {},
            "zero_variance_cols": [],
            "high_cardinality_cols": []
        }

        # Detección de centinelas por tipo
        numeric_sentinels = self.sentinels.get("numeric", [])
        object_sentinels = self.sentinels.get("object", [])
        datetime_sentinels = self.sentinels.get("datetime", [])

        for col in df.columns:
            # Centinelas
            counts = 0
            if pd.api.types.is_numeric_dtype(df[col]):
                counts = df[col].isin(numeric_sentinels).sum()
                # Varianza cero
                if df[col].nunique() <= 1:
                    quality["zero_variance_cols"].append(col)
            elif pd.api.types.is_object_dtype(df[col]):
                counts = df[col].isin(object_sentinels).sum()
                # Alta cardinalidad (ej. más del 50% de filas son únicas y hay muchas filas)
                unique_pct = df[col].nunique() / len(df) if len(df) > 0 else 0
                if unique_pct > 0.5 and len(df) > 50:
                    quality["high_cardinality_cols"].append(col)
            
            if counts > 0:
                quality["sentinel_counts"][col] = int(counts)

        return quality

    def _generate_profile(self, df: pd.DataFrame, table_name: str) -> Dict[str, Any]:
        """Perfilamiento estadístico detallado."""
        schema = self.schemas.get(table_name, {})
        profile = {"numeric": {}, "categorical": {}}

        for col in df.columns:
            expected_type = schema.get(col, "unknown")
            
            if expected_type in ["int", "float"] and pd.api.types.is_numeric_dtype(df[col]):
                desc = df[col].describe()
                p25 = float(desc["25%"])
                p75 = float(desc["75%"])
                iqr = p75 - p25
                lower_bound = p25 - 1.5 * iqr
                upper_bound = p75 + 1.5 * iqr
                
                outliers_below = int((df[col] < lower_bound).sum())
                outliers_above = int((df[col] > upper_bound).sum())

                profile["numeric"][col] = {
                    "mean": float(desc["mean"]),
                    "std": float(desc["std"]),
                    "min": float(desc["min"]),
                    "max": float(desc["max"]),
                    "p25": p25,
                    "p50": float(desc["50%"]),
                    "p75": p75,
                    "range": float(desc["max"] - desc["min"]),
                    "iqr_stats": {
                        "iqr": float(iqr),
                        "lower_bound": float(lower_bound),
                        "upper_bound": float(upper_bound),
                        "outliers_below": outliers_below,
                        "outliers_above": outliers_above,
                        "total_outliers": outliers_below + outliers_above
                    }
                }
            elif expected_type == "object" or pd.api.types.is_object_dtype(df[col]):
                if col == "fecha": continue # Saltar fecha de este análisis
                
                vc = df[col].value_counts()
                top_values = vc.head(5).to_dict()
                total = len(df[col])
                
                profile["categorical"][col] = {
                    "top_values": top_values,
                    "unique_count": int(df[col].nunique()),
                    "mode": str(vc.index[0]) if not vc.empty else None,
                    "top_weight": float(vc.iloc[0] / total) if not vc.empty and total > 0 else 0
                }

        return profile
