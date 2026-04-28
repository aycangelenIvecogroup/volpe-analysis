import streamlit as st
import pandas as pd
from pathlib import Path

# ==================================================
# PATHS
# ==================================================
BASE_PATH = Path(r"C:\Users\v47012b\OneDrive - Iveco Group\Documenti\volpe_analysis\data\raw")

FEB_FILE = BASE_PATH / "raw_agm02.xlsx"
MAR_FILE = BASE_PATH / "raw_agm03.xlsx"
BDG_FILE = BASE_PATH / "raw_agm_c12_2025.xlsx"

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
        df.columns = df.columns.str.strip().str.upper().str.replace("  ", " ")
        df["CUSTOMER MERGE"] = df["CUSTOMER MERGE"].astype(str).str.strip().str.upper()

        for c in ["ACT UNITS", "ACT TN", "ACT COGS"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")

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
    # UNIT METRICS (DOĞRU COST / PRICE)
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

    df["Δ TN (MAR - BDG)"] = df["MAR_TN"] - df["BDG_TN"]
    df["Δ COST (MAR - BDG)"] = df["MAR_COST"] - df["BDG_COST"]

    # --------------------------------------------------
    # CUSTOMER FILTER
    # --------------------------------------------------
    customers = st.multiselect(
        "Customer",
        sorted(df["CUSTOMER MERGE"].unique())
    )

    if customers:
        df = df[df["CUSTOMER MERGE"].isin(customers)]

    # --------------------------------------------------
    # COLUMN SELECTOR
    # --------------------------------------------------
    all_columns = [
        "CUSTOMER MERGE",

        "FEB_UNITS", "FEB_TN", "FEB_PRICE", "FEB_COST",
        "MAR_UNITS", "MAR_TN", "MAR_PRICE", "MAR_COST",
        "BDG_UNITS", "BDG_TN", "BDG_PRICE", "BDG_COST",

        "Δ TN (MAR - FEB)", "Δ COST (MAR - FEB)",
        "Δ TN (MAR - BDG)", "Δ COST (MAR - BDG)",
    ]

    default_columns = [
        "CUSTOMER MERGE",
        "MAR_TN", "MAR_PRICE", "MAR_COST",
        "BDG_PRICE", "BDG_COST",
        "Δ COST (MAR - BDG)",
    ]

    selected_columns = st.multiselect(
        "Columns to display",
        all_columns,
        default=default_columns,
    )

    # --------------------------------------------------
    # SAFE SORT ✅ (KEYERROR FIX)
    # --------------------------------------------------
    sort_col = "Δ COST (MAR - BDG)"
    display_df = df[selected_columns]

    if sort_col in display_df.columns:
        display_df = display_df.sort_values(sort_col, ascending=False)

    # --------------------------------------------------
    # TABLE
    # --------------------------------------------------
    st.dataframe(
        display_df,
        use_container_width=True,
        height=550,
    )
