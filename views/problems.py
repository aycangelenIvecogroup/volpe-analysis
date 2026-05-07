import streamlit as st
import pandas as pd
from pathlib import Path

# ==================================================
# PATHS (CLOUD SAFE)
# ==================================================
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"

FEB_FILE = RAW_DATA_DIR / "raw_agm02.xlsx"
MAR_FILE = RAW_DATA_DIR / "raw_agm03.xlsx"
BDG_FILE = RAW_DATA_DIR / "raw_agm_c12_2025.xlsx"

# ==================================================
# LOAD DATA
# ==================================================
@st.cache_data
def load_data():
    return (
        pd.read_excel(FEB_FILE, engine="openpyxl"),
        pd.read_excel(MAR_FILE, engine="openpyxl"),
        pd.read_excel(BDG_FILE, engine="openpyxl"),
    )

# ==================================================
# PAGE
# ==================================================
def render_problems():

    st.title("🚨 Problems")
    st.caption("Customer-level comparison (Feb / Mar / Budget)")
    st.divider()

    feb, mar, bdg = load_data()

    # --------------------------------------------------
    # NORMALIZATION
    # --------------------------------------------------
    for df in (feb, mar, bdg):
        df.columns = (
            df.columns
            .astype(str)
            .str.strip()
            .str.upper()
            .str.replace("  ", " ", regex=False)
        )
        df["CUSTOMER MERGE"] = (
            df["CUSTOMER MERGE"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        for c in ["ACT UNITS", "ACT TN", "ACT COGS"]:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    # --------------------------------------------------
    # AGGREGATION
    # --------------------------------------------------
    feb_agg = feb.groupby("CUSTOMER MERGE", as_index=False).agg(
        FEB_UNITS=("ACT UNITS", "sum"),
        FEB_TN=("ACT TN", "sum"),
        FEB_COGS=("ACT COGS", "sum"),
    )

    mar_agg = mar.groupby("CUSTOMER MERGE", as_index=False).agg(
        MAR_UNITS=("ACT UNITS", "sum"),
        MAR_TN=("ACT TN", "sum"),
        MAR_COGS=("ACT COGS", "sum"),
    )

    bdg_agg = bdg.groupby("CUSTOMER MERGE", as_index=False).agg(
        BDG_UNITS=("ACT UNITS", "sum"),
        BDG_TN=("ACT TN", "sum"),
        BDG_COGS=("ACT COGS", "sum"),
    )

    # --------------------------------------------------
    # MERGE
    # --------------------------------------------------
    df = (
        feb_agg
        .merge(mar_agg, on="CUSTOMER MERGE", how="left")
        .merge(bdg_agg, on="CUSTOMER MERGE", how="left")
    )

    # --------------------------------------------------
    # UNIT METRICS
    # --------------------------------------------------
    df["FEB_PRICE"] = df["FEB_TN"] / df["FEB_UNITS"]
    df["FEB_COST"] = df["FEB_COGS"] / df["FEB_UNITS"]

    df["MAR_PRICE"] = df["MAR_TN"] / df["MAR_UNITS"]
    df["MAR_COST"] = df["MAR_COGS"] / df["MAR_UNITS"]

    df["BDG_PRICE"] = df["BDG_TN"] / df["BDG_UNITS"]
    df["BDG_COST"] = df["BDG_COGS"] / df["BDG_UNITS"]

    # --------------------------------------------------
    # DELTAS
    # --------------------------------------------------
    df["Δ TN (MAR - FEB)"] = df["MAR_TN"] - df["FEB_TN"]
    df["Δ COST (MAR - FEB)"] = df["MAR_COST"] - df["FEB_COST"]
    df["Δ PRICE (MAR - FEB)"] = df["MAR_PRICE"] - df["FEB_PRICE"]

    df["Δ TN (MAR - BDG)"] = df["MAR_TN"] - df["BDG_TN"]
    df["Δ COST (MAR - BDG)"] = df["MAR_COST"] - df["BDG_COST"]
    df["Δ PRICE (MAR - BDG)"] = df["MAR_PRICE"] - df["BDG_PRICE"]


    # --------------------------------------------------
    # FILTERS
    # --------------------------------------------------
    customers = st.multiselect(
        "Customer",
        sorted(df["CUSTOMER MERGE"].unique())
    )

    if customers:
        df = df[df["CUSTOMER MERGE"].isin(customers)]

    # --------------------------------------------------
    # DISPLAY
    # --------------------------------------------------
    default_columns = [
        "CUSTOMER MERGE",
        "MAR_TN", "MAR_PRICE", "MAR_COST",
        "BDG_PRICE", "BDG_COST",
        "Δ COST (MAR - BDG)",
        "Δ PRICE (MAR - BDG)",
    ]

    display_df = df[default_columns].sort_values(
        "Δ COST (MAR - BDG)", ascending=False
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        height=550,
    )