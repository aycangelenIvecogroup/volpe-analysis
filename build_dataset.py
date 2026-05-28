import pandas as pd
from pathlib import Path

# 📁 dosya yolu
BASE_PATH = Path("data/clean excel files")

print("Loading files...")
def fix_customer(df):
    df["customer"] = (
        df["customer"]
        .astype(str)
        .str.strip()          # bosluk sil
        .str.upper()          # buyuk harf
        .str.replace("_", " ") # underscore temizle
    )
    return df

# ======================
# act04
# ======================
act04 = pd.read_excel(BASE_PATH / "c04_2026_clean.xlsx")

act04 = act04[["CUSTOMER MERGE", "tn", "agm"]].copy()
act04.columns = ["customer", "tn", "agm"]
act04["SCENARIO"] = "act04"
act04 = fix_customer(act04)

# ======================
# BDG
# ======================
bdg = pd.read_excel(BASE_PATH / "BDG2026_v4_clean.xlsx")

bdg = bdg[["CUSTOMER MERGE", "tn", "agm"]].copy()
bdg.columns = ["customer", "tn", "agm"]
bdg["SCENARIO"] = "BDG"
bdg = fix_customer(bdg)

# ======================
# LY
# ======================
ly = pd.read_excel(BASE_PATH / "LY25_clean.xlsx")

ly = ly[["CUSTOMER MERGE", "tn", "agm"]].copy()
ly.columns = ["customer", "tn", "agm"]
ly["SCENARIO"] = "LY"
ly = fix_customer(ly)

# ======================
# FCS
# ======================
fcs = pd.read_excel(BASE_PATH / "fcst1_2026_clean.xlsx")

fcs = fcs[["CUSTOMER MERGE", "tn", "agm"]].copy()
fcs.columns = ["customer", "tn", "agm"]
fcs["SCENARIO"] = "FCS1"
fcs = fix_customer(fcs)

# ======================
# CONCAT 4 DATASETS
# ======================
df = pd.concat([act04, bdg, ly, fcs], ignore_index=True)

# sayıya çevir
df["tn"] = pd.to_numeric(df["tn"], errors="coerce").fillna(0)
df["agm"] = pd.to_numeric(df["agm"], errors="coerce").fillna(0)

# ======================
# AGGREGATE (customer level)
# ======================
print("Aggregating...")

agg = df.groupby(["customer", "SCENARIO"]).agg({
    "tn": "sum",
    "agm": "sum"
}).reset_index()

pivot = agg.pivot(index="customer", columns="SCENARIO", values=["tn", "agm"])

# ✅ sadece complete data
pivot = pivot.dropna(subset=[
    ("tn", "act04"),
    ("tn", "BDG"),
    ("tn", "LY")
])

pivot.columns = [f"{m}_{s}" for m, s in pivot.columns]

pivot = pivot.reset_index()
pivot = pivot.sort_values("customer")



# ======================
# SAVE
# ======================
print("Saving dataset...")

pivot.to_parquet("core_dataset.parquet")

print("✅ DONE - dataset created!")