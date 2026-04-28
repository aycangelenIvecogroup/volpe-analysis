import pandas as pd


import pandas as pd


def load_monthly_actual(file_path: str, prefix: str):
    df = pd.read_excel(file_path)

    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace("  ", " ", regex=False)
    )

    numeric_cols = ["ACT UNITS", "ACT TN", "ACT AGM", "ACT SGM"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df = (
        df.groupby("CUSTOMER MERGE", as_index=False)
        .agg({
            "ACT UNITS": "sum",
            "ACT TN": "sum",
            "ACT AGM": "sum",
            "ACT SGM": "sum"
        })
        .rename(columns={
            "ACT UNITS": f"{prefix}_Units",
            "ACT TN": f"{prefix}_TN",
            "ACT AGM": f"{prefix}_AGM",
            "ACT SGM": f"{prefix}_SGM"
        })
    )

    return df


def load_budget_26(file_path: str):
    df = pd.read_excel(
        file_path,
        sheet_name="DB BDG_26",
        header=3
    )

    df.columns = df.columns.astype(str).str.strip()

    numeric_cols = ["UNITS", "TN", "AGM", "SGM", "GM+TARGET", "NS + TARGET"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df = (
        df[[
            "CUSTOMER MERGE",
            "UNITS",
            "TN",
            "AGM",
            "SGM",
            "GM+TARGET",
            "NS + TARGET"
        ]]
        .groupby("CUSTOMER MERGE", as_index=False)
        .sum()
        .rename(columns={
            "UNITS": "B26_Units",
            "TN": "B26_TN",
            "AGM": "B26_AGM",
            "SGM": "B26_SGM",
            "GM+TARGET": "B26_GM_TARGET",
            "NS + TARGET": "B26_NS_TARGET"
        })
    )

    return df


def load_forecast_26(file_path: str):
    df = pd.read_excel(file_path)

    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace("  ", " ", regex=False)
    )

    df = df[[
        "CUSTOMER MERGE",
        "UNITS",
        "TN",
        "AGM",
        "SGM"
    ]]

    for col in ["UNITS", "TN", "AGM", "SGM"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df = (
        df
        .groupby("CUSTOMER MERGE", as_index=False)
        .sum()
        .rename(columns={
            "UNITS": "FCST26_Units",
            "TN": "FCST26_TN",
            "AGM": "FCST26_AGM",
            "SGM": "FCST26_SGM"
        })
    )

    return df


def load_budget_26(file_path: str):
    """
    Load Budget 2026
    """

    df = pd.read_excel(
        file_path,
        sheet_name="DB BDG_26",
        header=3
    )

    df.columns = df.columns.astype(str).str.strip()

    numeric_cols = ["UNITS", "TN", "AGM", "SGM", "GM+TARGET", "NS + TARGET"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df = (
        df[[
            "CUSTOMER MERGE",
            "UNITS",
            "TN",
            "AGM",
            "SGM",
            "GM+TARGET",
            "NS + TARGET"
        ]]
        .groupby("CUSTOMER MERGE", as_index=False)
        .sum()
        .rename(columns={
            "UNITS": "B26_Units",
            "TN": "B26_TN",
            "AGM": "B26_AGM",
            "SGM": "B26_SGM",
            "GM+TARGET": "B26_GM_TARGET",
            "NS + TARGET": "B26_NS_TARGET"
        })
    )

    return df


import pandas as pd


def load_monthly_actual(file_path: str, prefix: str):
    df = pd.read_excel(file_path)

    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace("  ", " ", regex=False)
    )

    numeric_cols = ["ACT UNITS", "ACT TN", "ACT AGM", "ACT SGM"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df = (
        df.groupby("CUSTOMER MERGE", as_index=False)
        .agg({
            "ACT UNITS": "sum",
            "ACT TN": "sum",
            "ACT AGM": "sum",
            "ACT SGM": "sum"
        })
        .rename(columns={
            "ACT UNITS": f"{prefix}_Units",
            "ACT TN": f"{prefix}_TN",
            "ACT AGM": f"{prefix}_AGM",
            "ACT SGM": f"{prefix}_SGM"
        })
    )

    return df


def load_budget_26(file_path: str):
    df = pd.read_excel(
        file_path,
        sheet_name="DB BDG_26",
        header=3
    )

    df.columns = df.columns.astype(str).str.strip()

    numeric_cols = ["UNITS", "TN", "AGM", "SGM", "GM+TARGET", "NS + TARGET"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df = (
        df[[
            "CUSTOMER MERGE",
            "UNITS",
            "TN",
            "AGM",
            "SGM",
            "GM+TARGET",
            "NS + TARGET"
        ]]
        .groupby("CUSTOMER MERGE", as_index=False)
        .sum()
        .rename(columns={
            "UNITS": "B26_Units",
            "TN": "B26_TN",
            "AGM": "B26_AGM",
            "SGM": "B26_SGM",
            "GM+TARGET": "B26_GM_TARGET",
            "NS + TARGET": "B26_NS_TARGET"
        })
    )

    return df


def load_forecast_26(file_path: str):
    # ✅ Header ikinci satır
    df = pd.read_excel(file_path, header=1)

    # ✅ Kolonları normalize et
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
        "SGM": "SGM"
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
            "SGM": "FCST26_SGM"
        })
    )

    return df
