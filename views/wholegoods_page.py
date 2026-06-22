import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

BASE_PATH = Path("data/clean excel files")

# ======================
# HELPERS
# ======================
def euro(x):
    if pd.isna(x):
        return ""
    if abs(x) >= 1_000_000:
        return f"€{x/1_000_000:.1f}M"
    elif abs(x) >= 1_000:
        return f"€{x/1_000:.1f}K"
    return f"€{x:.0f}"

def number(x):
    if pd.isna(x):
        return ""
    return f"{int(x):,}"

# ======================
# LOAD WHOLEGOODS ✅
# ======================
@st.cache_data
def load_wholegoods():

    def prep(file, scenario):
        df = pd.read_excel(BASE_PATH / file)
        df.columns = df.columns.str.strip().str.upper()

        df = df.rename(columns={
            "CUSTOMER MERGE": "customer",
            "TN": "tn",
            "AGM": "agm",
            "UNITS": "units"
        })

        df["customer"] = df["customer"].astype(str).str.strip().str.upper()

        for col in ["tn", "agm", "units"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.fillna(0)

        df = df.groupby("customer", as_index=False)[
            ["tn", "agm", "units"]
        ].sum()

        df["SCENARIO"] = scenario

        return df

    act = prep("c04_2026_clean.xlsx", "ACT")
    fcs = prep("fcst1_2026_clean.xlsx", "FCS1")

    ly  = prep("LY25_clean.xlsx", "LY")

    df = pd.concat([act, fcs, ly], ignore_index=True)

    return df

# ======================
# PAGE ✅
# ======================
def render_wholegoods_page():

    st.title("📊 Wholegoods Overview")

    df = load_wholegoods()

    selected_customers = st.multiselect(
        "Select Customers",
        sorted(df["customer"].unique())
    )

    # ======================
    # PIVOT
    # ======================
    pivot = df.pivot(
        index="customer",
        columns="SCENARIO",
        values=["tn", "agm", "units"]
    ).fillna(0)

    pivot.columns = [f"{m}_{s}" for m, s in pivot.columns]
    pivot = pivot.reset_index()

    # ✅ SAFE COLUMNS
    for c in [
        "tn_ACT","tn_FCS1",
        "agm_ACT","agm_FCS1",
        "units_ACT","units_FCS1",
        "tn_LY","agm_LY"
    ]:
        if c not in pivot.columns:
            pivot[c] = 0

    # ======================
    # FILTER
    # ======================
    if selected_customers:
        pivot = pivot[pivot["customer"].isin(selected_customers)]

    # ======================
    # CALC
    # ======================
    pivot["margin_ACT"] = pivot["agm_ACT"] / pivot["tn_ACT"].replace(0, np.nan)
    pivot["margin_FCS1"] = pivot["agm_FCS1"] / pivot["tn_FCS1"].replace(0, np.nan)
    pivot["margin_LY"] = pivot["agm_LY"] / pivot["tn_LY"].replace(0, np.nan)
    pivot["Δ_FCS1"] = (pivot["margin_ACT"] - pivot["margin_FCS1"]) * 100
    pivot["Δ_LY"] = (pivot["margin_ACT"] - pivot["margin_LY"]) * 100


    pivot = pivot.sort_values("Δ_FCS1")

    # ======================
    # TABLE
    # ======================
    rows = []

    for _, r in pivot.iterrows():

        rows.append({

            "Customer": r["customer"],

            # Volume
            "Vol ACT": number(r["units_ACT"]),
            "Vol FCS1": number(r["units_FCS1"]),
            "Vol LY": number(r["units_LY"]),

            # Revenue
            "NS ACT": euro(r["tn_ACT"]),
            "NS FCS1": euro(r["tn_FCS1"]),
            "NS LY": euro(r["tn_LY"]),

            # Profit
            "AGM ACT": euro(r["agm_ACT"]),
            "AGM FCS1": euro(r["agm_FCS1"]),
            "AGM LY": euro(r["agm_LY"]),

            # Margin
            "Margin ACT": f"{r['margin_ACT']*100:.1f}%" if pd.notna(r["margin_ACT"]) else "",
            "Margin FCS1": f"{r['margin_FCS1']*100:.1f}%" if pd.notna(r["margin_FCS1"]) else "",
            "Margin LY": f"{r['margin_LY']*100:.1f}%" if pd.notna(r["margin_LY"]) else "",

            # Delta
            "Δ FCS1": f"{r['Δ_FCS1']:+.1f} pp",
            "Δ LY": f"{r['Δ_LY']:+.1f} pp",

        })

    final_df = pd.DataFrame(rows)

    # ======================
    # STYLE
    # ======================
    def highlight(val):
        try:
            v = float(str(val).replace("pp","").replace("%",""))
        except:
            return ""

        if v > 2:
            return "background-color:#c6f7d0"
        elif v < -2:
            return "background-color:#f7c6c7"
        else:
            return "background-color:#fff3cd"

    st.dataframe(
        final_df.style.map(
            highlight,
            subset=["Δ FCS1","Δ LY"]
        ),
        use_container_width=True,
        height=700
    )

