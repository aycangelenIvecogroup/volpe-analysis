import pandas as pd


def compute_kpis(df: pd.DataFrame, prefix: str) -> pd.DataFrame:
    """
    Compute standard KPIs for a given prefix
    Example prefixes: March, February, B26, AGM25
    """

    df[f"{prefix}_AGM%"] = (df[f"{prefix}_AGM"] / df[f"{prefix}_TN"]) * 100
    df[f"{prefix}_SGM%"] = (df[f"{prefix}_SGM"] / df[f"{prefix}_TN"]) * 100

    df[f"{prefix}_IndBalance"] = df[f"{prefix}_SGM"] - df[f"{prefix}_AGM"]
    df[f"{prefix}_IndBalance_Density%"] = (
        df[f"{prefix}_IndBalance"] / df[f"{prefix}_TN"] * 100
    )

    return df
def compute_coverage_vs_budget(df, prefix):
    tn_col = f"{prefix}_TN"
    cov_col = f"{prefix}_Coverage_vs_B26%"

    if tn_col not in df.columns or "B26_TN" not in df.columns:
        return df  # silently skip if not applicable

    df[cov_col] = (df[tn_col] / df["B26_TN"]) * 100

    return df



def compute_gaps(df: pd.DataFrame) -> pd.DataFrame:
    """
    Budget & Year-on-Year gap analysis
    """

    df["GAP_March_vs_B26_AGM%"] = df["March_AGM%"] - df["B26_AGM%"]
    df["YoY_March_vs_AGM25_AGM%"] = df["March_AGM%"] - df["AGM25_AGM%"]

    def gap_flag(x):
        if x < -3:
            return "CRITICAL"
        elif x < 0:
            return "WARNING"
        else:
            return "OK"

    df["March_vs_B26_Flag"] = df["GAP_March_vs_B26_AGM%"].apply(gap_flag)

    return df