import pandas as pd
from data_loader import (
    load_monthly_actual,
    load_budget_26,
    load_forecast_26
)
from analysis_engine import (
    compute_kpis,
    compute_gaps,
    compute_coverage_vs_budget
)

# ----------------------------
# LOAD DATA
# ----------------------------

df_march = load_monthly_actual("AGM_C03.xlsx", "March")
df_feb = load_monthly_actual("volpe_February.xlsx", "February")
df_f25 = load_monthly_actual("agm_25.xlsx", "AGM25")
df_b26 = load_budget_26("DB BDG_26_AGM_SIP_v2_sent.xlsx")
df_fcst = load_forecast_26("DB_Forecast1_Volpe.xlsx")

# ----------------------------
# MERGE ALL
# ----------------------------

df = (
    df_march
    .merge(df_feb, on="CUSTOMER MERGE", how="left")
    .merge(df_f25, on="CUSTOMER MERGE", how="left")
    .merge(df_b26, on="CUSTOMER MERGE", how="left")
    .merge(df_fcst, on="CUSTOMER MERGE", how="left")
    .fillna(0)
)

# ----------------------------
# KPI ENGINE
# ----------------------------

df = compute_kpis(df, "March")
df = compute_kpis(df, "February")
df = compute_kpis(df, "AGM25")
df = compute_kpis(df, "B26")
df = compute_kpis(df, "FCST26")

df = compute_gaps(df)
df = compute_coverage_vs_budget(df, "March")
df = compute_coverage_vs_budget(df, "February")
df = compute_coverage_vs_budget(df, "AGM25")
df = compute_coverage_vs_budget(df, "FCST26")


# ----------------------------
# ROUNDING
# ----------------------------

pct_cols = [c for c in df.columns if c.endswith("%")]
df[pct_cols] = df[pct_cols].round(1)

df = df.replace([float("inf"), -float("inf")], 0)

# ---- FINAL COLUMN STANDARDIZATION (MANDATORY) ----
df.columns = (
    df.columns
    .astype(str)
    .str.strip()
    .str.replace("_pct", "%", regex=False)
)

# ----------------------------
# EXPORT
# ----------------------------

df.to_excel("customer_amount_layer_clean.xlsx", index=False)

print("✅ Analysis dataset created successfully (ACT + B26 + FCST26)")