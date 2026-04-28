import pandas as pd
from pathlib import Path


# ==================================================
# PATH CONFIG
# ==================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

ACT_FILE = DATA_DIR / "AGM_C03.xlsx"
AGM25_FILE = DATA_DIR / "agm_25.xlsx"
BDG26_FILE = DATA_DIR / "DB BDG_26_AGM_SIP_v2_sent.xlsx"
OUTPUT_FILE = DATA_DIR / "customer_amount_layer_clean.xlsx"


# ==================================================
# 1. LOAD & PREP – MARCH ACT
# ==================================================
df_act_raw = pd.read_excel(ACT_FILE)

df_act_raw.columns = (
    df_act_raw.columns.astype(str)
    .str.strip()
    .str.replace("  ", " ", regex=False)
)

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

base_customers = df_act["CUSTOMER MERGE"]
print("✅ March ACT prepared:", df_act.shape)


# ==================================================
# 2. AGM25
# ==================================================
df_agm25_raw = pd.read_excel(AGM25_FILE)

df_agm25_raw.columns = (
    df_agm25_raw.columns.astype(str)
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
    BDG26_FILE,
    sheet_name="DB BDG_26",
    header=3
)

df_bdg_raw.columns = (
    df_bdg_raw.columns.astype(str)
    .str.strip()
    .str.replace("  ", " ", regex=False)
)

df_bdg = (
    df_bdg_raw[
        [
            "CUSTOMER MERGE",
            "UNITS",
            "TN",
            "AGM",
            "SGM",
            "GM+TARGET",
            "NS + TARGET"
        ]
    ]
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
    .fillna(0)
)

print("✅ FINAL dataset shape:", df_final.shape)


# ==================================================
# 5. KPI CALCULATIONS
# ==================================================
def compute_kpis(df, prefix):
    df[f"{prefix}_AGM%"] = df[f"{prefix}_AGM"] / df[f"{prefix}_TN"] * 100
    df[f"{prefix}_SGM%"] = df[f"{prefix}_SGM"] / df[f"{prefix}_TN"] * 100
    return df

df_final = compute_kpis(df_final, "March")
df_final = compute_kpis(df_final, "AGM25")

df_final["BDG26_AGM%"] = df_final["BDG26_AGM"] / df_final["BDG26_TN"] * 100
df_final["BDG26_SGM%"] = df_final["BDG26_SGM"] / df_final["BDG26_TN"] * 100

df_final = df_final.replace([float("inf"), -float("inf")], 0)


# ==================================================
# 6. ROUNDING
# ==================================================
df_final = df_final.round(1)


# ==================================================
# 7. EXPORT
# ==================================================
df_final.to_excel(OUTPUT_FILE, index=False)
print("✅ customer_amount_layer_clean.xlsx created:", OUTPUT_FILE)