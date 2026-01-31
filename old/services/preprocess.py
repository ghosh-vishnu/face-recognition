from typing import Dict, Any, List
import pandas as pd
import numpy as np

TYPE_CONSISTENCY_THRESHOLD = 0.8


def profile_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    if df.empty:
        return {
            "shape": {"rows": 0, "columns": 0},
            "missing": {},
            "duplicates": 0,
            "inferred_types": {},
            "type_consistency": {},
            "numeric_columns": [],
            "categorical_columns": [],
            "outliers": {},
            "suggestions": ["Empty dataset"]
        }
    missing_summary = df.isna().sum().to_dict()
    duplicate_count = int(df.duplicated().sum())
    inferred_types = df.dtypes.apply(lambda x: str(x)).to_dict()
    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_columns = df.select_dtypes(include=["object", "category"]).columns.tolist()
    
    def is_numeric_like(v):
        try:
            float(v)
            return True
        except (TypeError, ValueError):
            return False


    type_consistency = {
        col: float(df[col].map(is_numeric_like).mean())
        if df[col].dtype == "object"
        else 1.0
        for col in df.columns
    }

    outlier_columns = {}
    for col in numeric_columns:
        series = df[col].dropna()
        if series.empty:
            continue
        q1, q3 = series.quantile([0.25, 0.75])
        iqr = q3 - q1
        if iqr == 0:
            continue
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        outlier_columns[col] = int(((series < lower) | (series > upper)).sum())

    suggestions = []
    if any(count > 0 for count in missing_summary.values()):
        suggestions.append("Use median/most-frequent imputation for missing values.")
    if duplicate_count > 0:
        suggestions.append("Drop duplicate rows while retaining the first occurrence.")
    for col, consistency in type_consistency.items():
        if consistency < TYPE_CONSISTENCY_THRESHOLD:
            suggestions.append(f"Column '{col}' has inconsistent types; normalize values.")
    if not suggestions:
        suggestions.append("Dataset looks healthy. No major issues identified.")

    return {
        "shape": {
        "rows": df.shape[0],
        "columns": df.shape[1]
        },
        "missing": missing_summary,
        "duplicates": duplicate_count,
        "inferred_types": inferred_types,
        "type_consistency": type_consistency,
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "outliers": outlier_columns,
        "suggestions": suggestions,
    }


def apply_auto_clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for column in df.columns:
        if df[column].dtype == "object":
            df[column] = df[column].replace(["", "NA", "N/A", "null"], None)
    for column in df.select_dtypes(include=[np.number]).columns:
        if df[column].isna().mean() > 0:
            df[column] = df[column].fillna(df[column].median())
    for column in df.select_dtypes(include=["object", "category"]).columns:
        if df[column].isna().mean() > 0:
            df[column] = df[column].fillna(df[column].mode().iloc[0])
    df = df.drop_duplicates()
    return df


def compute_quality_score(profile: Dict[str, Any]) -> float:
    total_cells = profile["shape"]["rows"] * profile["shape"]["columns"]
    missing_penalty = (
        sum(profile["missing"].values()) / total_cells if total_cells else 0
    )
    duplicate_penalty = min(profile["duplicates"] / max(profile["shape"]["rows"], 1), 1)
    type_penalty = (
        1- np.mean(list(profile["type_consistency"].values()))
        if profile["type_consistency"]
        else 0
    )
    outlier_penalty = (
    sum(profile["outliers"].values())/ max(profile["shape"]["rows"] * max(len(profile["numeric_columns"]), 1), 1) if profile["numeric_columns"] else 0)
    raw_score = 1 - (0.4 * missing_penalty + 0.2 * duplicate_penalty + 0.2 * type_penalty + 0.2 * outlier_penalty)
    return round(max(min(raw_score * 100, 100), 0), 2)

