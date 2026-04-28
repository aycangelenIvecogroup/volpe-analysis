# ==================================================
# KPI & COLUMN HELP TEXTS (CENTRALIZED)
# ==================================================

HELP = {
    # --- GENERIC KPIs ---
    "agm_pct": "Adjusted Gross Margin (AGM) as a percentage of Net Sales (TN).",
    "sgm_pct": "Standard Gross Margin (SGM) as a percentage of Net Sales (TN).",
    "coverage_pct": (
        "Sales execution indicator: Actual Net Sales (TN) "
        "divided by Budget 2026 Net Sales."
    ),
    "units": "Number of units sold in the selected period.",
    "tn": "Total Net Sales (TN) value for the selected period.",

    # --- DERIVED / COMPARISON ---
    "agm_gap_b26": "Difference between actual AGM% and Budget 2026 AGM%.",
    "agm_yoy": "Year-over-year change in AGM% versus 2025.",
    "sales_gap": "Remaining gap to reach 100% budget coverage.",

    # --- RISK ---
    "risk_level": (
        "Risk classification based on Coverage % thresholds "
        "(CRITICAL / WARNING / OK)."
    ),

    # --- TABLE COLUMNS ---
    "customer": "End customer / OEM / grouped customer entity."
}


def h(key: str) -> str:
    """
    Shorthand accessor for help texts.
    Safe: returns empty string if key not found.
    """
    return HELP.get(key, "")


# ==================================================
# MANAGEMENT INTERPRETATION (OVERVIEW)
# ==================================================

def explain_overview(df, month: str, critical_below: float):
    """
    Generate human-readable management interpretation
    for the Overview page.
    """

    agm_col = f"{month}_AGM%"
    coverage_col = f"{month}_Coverage_vs_B26%"

    explanations = []

    avg_coverage = df[coverage_col].mean()
    avg_agm = df[agm_col].mean()
    critical_count = (df[coverage_col] < critical_below).sum()

    if avg_coverage < 100:
        explanations.append(
            "Overall sales execution is **below plan**, "
            "indicating a **volume-related risk**."
        )

    if avg_agm < 0:
        explanations.append(
            "Average margin is negative, pointing to "
            "**structural profitability issues**."
        )

    if critical_count > 0:
        explanations.append(
            f"There are **{critical_count} customers in CRITICAL status** "
            "requiring immediate attention."
        )

    if not explanations:
        explanations.append(
            "Sales execution and profitability are broadly "
            "**in line with targets**."
        )

    return explanations