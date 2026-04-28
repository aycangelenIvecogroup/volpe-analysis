import pandas as pd

# ==================================================
# 1. LOAD & PREP – MARCH ACT (BASE FILE)
# ==================================================

df_act_raw = pd.read_excel("AGM_C03.xlsx.xlsx")

df_act_raw.columns = (
    df_act_raw.columns
    .astype(str)
    .str.strip()
    .str.replace("  ", " ", regex=False)
)

# ✅ DEBUG (isteğe bağlı, 1 kere çalıştır)
print("ACT columns:", df_act_raw.columns.tolist())

df_act = (
    df_act_raw
    .groupby("CUSTOMER MERGE", as_index=False)
    .agg({
        "ACT UNITS": "sum",
        "ACT TN": "sum",
        "ACT AGM": "sum",
        "ACT SGM": "sum"
    })
    .rename(columns={
        "ACT UNITS": "March_Units",
        "ACT TN": "March_TN",
        "ACT AGM": "March_AGM",
        "ACT SGM": "March_SGM"
    })
)

print("✅ March ACT base created:", df_act.shape)

base_customers = df_act["CUSTOMER MERGE"]

# ==================================================
# 2. AGM25
# ==================================================

df_agm25_raw = pd.read_excel("agm_25.xlsx")

df_agm25_raw.columns = (
    df_agm25_raw.columns
    .astype(str)
    .str.strip()
    .str.replace("  ", " ", regex=False)
)

df_agm25 = (
    df_agm25_raw
    .groupby("CUSTOMER MERGE", as_index=False)
    .agg({
        "ACT UNITS": "sum",
        "ACT TN": "sum",
        "ACT AGM": "sum",
        "ACT SGM": "sum"
    })
    .rename(columns={
        "ACT UNITS": "AGM25_Units",
        "ACT TN": "AGM25_TN",
        "ACT AGM": "AGM25_AGM",
        "ACT SGM": "AGM25_SGM"
    })
)

df_agm25 = df_agm25[df_agm25["CUSTOMER MERGE"].isin(base_customers)]

print("✅ AGM25 prepared:", df_agm25.shape)

# ==================================================
# 3. BDG26
# ==================================================

df_bdg_raw = pd.read_excel(
    "DB BDG_26_AGM_SIP_v2_sent.xlsx",
    sheet_name="DB BDG_26",
    header=3
)

df_bdg_raw.columns = (
    df_bdg_raw.columns
    .astype(str)
    .str.strip()
    .str.replace("  ", " ", regex=False)
)

df_bdg = (
    df_bdg_raw[[
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
        "UNITS": "BDG26_Units",
        "TN": "BDG26_TN",
        "AGM": "BDG26_AGM",
        "SGM": "BDG26_SGM",
        "GM+TARGET": "BDG26_GM_TARGET",
        "NS + TARGET": "BDG26_NS_TARGET"
    })
)

df_bdg = df_bdg[df_bdg["CUSTOMER MERGE"].isin(base_customers)]

print("✅ BDG26 prepared:", df_bdg.shape)

# ==================================================
# 4. FINAL MERGE
# ==================================================

df_final = (
    df_act
    .merge(df_agm25, on="CUSTOMER MERGE", how="left")
    .merge(df_bdg, on="CUSTOMER MERGE", how="left")
)

df_final = df_final.fillna(0)

print("✅ FINAL dataset shape:", df_final.shape)

# ==================================================
# ROUND NUMERIC COLUMNS (max 1 decimal)
# ==================================================
# ==================================================
# CALCULATIONS – MARCH
# ==================================================

def compute_kpis(df, prefix):
    df[f"{prefix}_AGM%"] = (df[f"{prefix}_AGM"] / df[f"{prefix}_TN"]) * 100
    df[f"{prefix}_SGM%"] = (df[f"{prefix}_SGM"] / df[f"{prefix}_TN"]) * 100

    df[f"{prefix}_IndBalance"] = df[f"{prefix}_SGM"] - df[f"{prefix}_AGM"]
    df[f"{prefix}_IndBalance_Density%"] = (
        df[f"{prefix}_IndBalance"] / df[f"{prefix}_TN"] * 100
    )

    return df

# ==================================================
# CALCULATIONS – BDG26
# ==================================================

df_final["BDG26_AGM_pct"] = df_final["BDG26_AGM"] / df_final["BDG26_TN"]
df_final["BDG26_SGM_pct"] = df_final["BDG26_SGM"] / df_final["BDG26_TN"]

df_final["BDG26_IndBalance"] = df_final["BDG26_SGM"] - df_final["BDG26_AGM"]
df_final["BDG26_IndBalance_Density"] = (
    df_final["BDG26_IndBalance"] / df_final["BDG26_TN"]
)

# ==================================================
# CALCULATIONS – AGM25
# ==================================================

df_final["AGM25_AGM_pct"] = df_final["AGM25_AGM"] / df_final["AGM25_TN"]
df_final["AGM25_SGM_pct"] = df_final["AGM25_SGM"] / df_final["AGM25_TN"]

df_final["AGM25_IndBalance"] = df_final["AGM25_SGM"] - df_final["AGM25_AGM"]
df_final["AGM25_IndBalance_Density"] = (
    df_final["AGM25_IndBalance"] / df_final["AGM25_TN"]
)
cols_to_round = [
    "March_Units", "March_TN", "March_AGM", "March_SGM",
    "AGM25_Units", "AGM25_TN", "AGM25_AGM", "AGM25_SGM",
    "BDG26_Units", "BDG26_TN", "BDG26_AGM", "BDG26_SGM",
    "BDG26_GM_TARGET", "BDG26_NS_TARGET"
]
# ==================================================
# ROUND ALL KPI COLUMNS (max 1 decimal)
# ==================================================

kpi_cols = [
    "March_AGM_pct", "March_SGM_pct", "March_IndBalance_Density",
    "BDG26_AGM_pct", "BDG26_SGM_pct", "BDG26_IndBalance_Density",
    "AGM25_AGM_pct", "AGM25_SGM_pct", "AGM25_IndBalance_Density"
]

df_final[kpi_cols] = (df_final[kpi_cols] * 100).round(1)

df_final = df_final.replace([float("inf"), -float("inf")], 0)
df_final[cols_to_round] = df_final[cols_to_round].round(1)

# ==================================================
# 5. EXPORT
# ==================================================

df_final.to_excel("customer_amount_layer_clean.xlsx", index=False)

print("✅ customer_amount_layer_clean.xlsx created")