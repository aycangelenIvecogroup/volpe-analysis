import pandas as pd
from pathlib import Path


# ==================================================
# GENERIC HELPERS
# ==================================================

def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace("\n", " ", regex=False)
        .str.replace("  ", " ", regex=False)
    )
    return df


# ==================================================
# LOAD MONTHLY ACTUALS (ACT / AGM25 etc.)
# ==================================================

def load_monthly_actual(file_path: str | Path, prefix: str) -> pd.DataFrame:
    """
    Load monthly actuals (ACT, AGM25, etc.)
    """
    df = pd.read_excel(file_path)
    df = _clean_columns(df)

    numeric_cols = ["ACT UNITS", "ACT TN", "ACT AGM", "ACT SGM"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df = (
        df.groupby("CUSTOMER MERGE", as_index=False)
        .agg({
            "ACT UNITS": "sum",
            "ACT TN": "sum",
            "ACT AGM": "sum",
            "ACT SGM": "sum",
        })
        .rename(columns={
            "ACT UNITS": f"{prefix}_Units",
            "ACT TN": f"{prefix}_TN",
            "ACT AGM": f"{prefix}_AGM",
            "ACT SGM": f"{prefix}_SGM",
        })
    )

    return df


# ==================================================
# LOAD BUDGET 2026
# ==================================================

def load_budget_26(file_path: str | Path) -> pd.DataFrame:
    """
    Load Budget 2026 file.
    """
    df = pd.read_excel(
        file_path,
        sheet_name="DB BDG_26",
        header=3
    )

    df = _clean_columns(df)

    numeric_cols = ["UNITS", "TN", "AGM", "SGM", "GM+TARGET", "NS + TARGET"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df = (
        df[
            [
                "CUSTOMER MERGE",
                "UNITS",
                "TN",
                "AGM",
                "SGM",
                "GM+TARGET",
                "NS + TARGET",
            ]
        ]
        .groupby("CUSTOMER MERGE", as_index=False)
        .sum()
        .rename(columns={
            "UNITS": "B26_Units",
            "TN": "B26_TN",
            "AGM": "B26_AGM",
            "SGM": "B26_SGM",
            "GM+TARGET": "B26_GM_TARGET",
            "NS + TARGET": "B26_NS_TARGET",
        })
    )

    return df


# ==================================================
# LOAD FORECAST 2026
# ==================================================

def load_forecast_26(file_path: str | Path) -> pd.DataFrame:
    """
    Load 2026 forecast file.
    """
    df = pd.read_excel(file_path, header=1)

    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.upper()
        .str.replace("\n", " ", regex=False)
        .str.replace("  ", " ", regex=False)
        .str.replace(" ", "_")
    )

    required_cols = {
        "CUSTOMER_MERGE": "CUSTOMER MERGE",
        "FY_UNITS": "UNITS",
        "FY_TN": "TN",
        "AGM": "AGM",
        "SGM": "SGM",
    }

    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Forecast file missing columns: {missing}")

    df = df[list(required_cols.keys())].rename(columns=required_cols)

    for col in ["UNITS", "TN", "AGM", "SGM"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df = (
        df.groupby("CUSTOMER MERGE", as_index=False)
        .sum()
        .rename(columns={
            "UNITS": "FCST26_Units",
            "TN": "FCST26_TN",
            "AGM": "FCST26_AGM",
            "SGM": "FCST26_SGM",
        })
    )

    return df
