import streamlit as st
import pandas as pd
from pathlib import Path

BASE_PATH = Path("data/raw")


# ==================================================
# CLEAN
# ==================================================
def clean_columns(df):
    df.columns = (
        df.columns.astype(str)
        .str.replace("\n", " ")
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
        .str.upper()
    )
    return df


# ==================================================
# LOAD DATA
# ==================================================
@st.cache_data
def load_data():

    def load_file(path, scenario):
        df = pd.read_excel(path)
        df = clean_columns(df)

        df = df.rename(columns={

            "CUSTOMER MERGE": "customer",
            "PRODUCT": "product",
            "PN ALLESTIMENTO": "pn",

            "ACT UNITS": "units",
            "UNITS": "units",
            "FY UNITS": "units",

            "ACT TN": "tn",
            "TN": "tn",
            "FY TN": "tn",

            "ACT COGS": "cogs",
            "COGS": "cogs",
            "FY COGS": "cogs",

            "ACT AGM": "agm",
            "AGM": "agm",

            "ACT VCE": "vce",
            "VCE": "vce",
            "FY VCE": "vce",
            "ACT SGM": "sgm",
            "SGM": "sgm",


        })

        df["SCENARIO"] = scenario
        return df

    march = load_file(BASE_PATH / "raw_agm03.xlsx", "MARCH")
    bdg = load_file(BASE_PATH / "raw_bdg26.xlsx", "BDG")

    df = pd.concat([march, bdg])

    for c in ["units", "tn", "cogs", "agm", "vce", "sgm"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    return df


# ==================================================
# PAGE
# ==================================================
def render_unit_bridge():

    st.title("🧩 Unit Price Breakdown (ACT vs BDG)")

    df = load_data()

    # ===============================
    # CUSTOMER SELECT
    # ===============================
    customer = st.selectbox(
        "Select Customer",
        sorted(df["customer"].dropna().unique())
    )

    df = df[df["customer"] == customer]

    # ===============================
    # PN SELECT
    # ===============================
    pn = st.selectbox(
        "Select PN",
        sorted(df["pn"].dropna().unique())
    )

    df = df[df["pn"] == pn]

    # ===============================
    # AGGREGATION
    # ===============================
    df_group = df.groupby(["SCENARIO"], as_index=False)[
        ["units", "tn", "cogs", "agm", "vce", "sgm"]
    ].sum()

    df_group = df_group.set_index("SCENARIO")

    # ===============================
    # CALCULATIONS
    # ===============================
    def calc_unit(row):
        units = row["units"] if row["units"] != 0 else 1

        unit_price = row["tn"] / units
        unit_cogs = row["cogs"] / units
        unit_agm = row["agm"] / units

        unit_vce = row["vce"] / units if "vce" in row else 0
        unit_var = unit_price - unit_cogs - unit_vce - unit_agm

        return pd.Series({
            "unit_price": unit_price,
            "unit_cogs": unit_cogs,
            "unit_vce": unit_vce,
            "unit_var": unit_var,
            "unit_agm": unit_agm
        })

    unit_df = df_group.apply(calc_unit, axis=1)

    # ===============================
    # BUILD TABLE
    # ===============================
    scenarios = ["MARCH", "BDG"]

    data = []
    metrics = ["unit_price", "unit_cogs", "unit_vce", "unit_var", "unit_agm"]

    names = {
        "unit_price": "Unit Price",
        "unit_cogs": "COGS",
        "unit_vce": "VCE",
        "unit_var": "VAR",
        "unit_agm": "AGM"
    }

    for m in metrics:

        act_val = unit_df.loc["MARCH", m] if "MARCH" in unit_df.index else 0
        bdg_val = unit_df.loc["BDG", m] if "BDG" in unit_df.index else 0

        data.append({
            "Metric": names[m],
            "ACT": act_val,
            "BDG": bdg_val,
            "Δ": act_val - bdg_val
        })

    result = pd.DataFrame(data)

    # ==================================================
    # ADD AGM %
    # ==================================================
    if "MARCH" in df_group.index and df_group.loc["MARCH", "tn"] != 0:
        act_margin = df_group.loc["MARCH", "agm"] / df_group.loc["MARCH", "tn"]
    else:
        act_margin = 0

    if "BDG" in df_group.index and df_group.loc["BDG", "tn"] != 0:
        bdg_margin = df_group.loc["BDG", "agm"] / df_group.loc["BDG", "tn"]
    else:
        bdg_margin = 0

    margin_row = pd.DataFrame([{
        "Metric": "AGM %",
        "ACT": act_margin * 100,
        "BDG": bdg_margin * 100,
        "Δ": (act_margin - bdg_margin) * 100
    }])

    result = pd.concat([result, margin_row], ignore_index=True)

    # ==================================================
    # ADD SGM %
    # ==================================================
    if "MARCH" in df_group.index and df_group.loc["MARCH", "tn"] != 0:
        act_sgm_margin = df_group.loc["MARCH", "sgm"] / df_group.loc["MARCH", "tn"]
    else:
        act_sgm_margin = 0

    if "BDG" in df_group.index and df_group.loc["BDG", "tn"] != 0:
        bdg_sgm_margin = df_group.loc["BDG", "sgm"] / df_group.loc["BDG", "tn"]
    else:
        bdg_sgm_margin = 0

    sgm_row = pd.DataFrame([{
        "Metric": "SGM %",
        "ACT": act_sgm_margin * 100,
        "BDG": bdg_sgm_margin * 100,
        "Δ": (act_sgm_margin - bdg_sgm_margin) * 100
    }])

    result = pd.concat([result, sgm_row], ignore_index=True)

    # ===============================
    # DISPLAY
    # ===============================
    st.subheader(f"{customer} | {pn}")
    def color_delta(val):
        if val > 0:
            return "color: green"
        elif val < 0:
            return "color: red"
        return ""

    def color_delta_row(row, df_ref):
        val = row["Δ"]
        metric = df_ref.loc[row.name, "Metric"]

        positive_good = True

        if metric in ["COGS", "VCE"]:
            positive_good = False
        elif metric == "VAR":
            positive_good = False

        if val > 0:
            return ["color: green" if positive_good else "color: red"]
        elif val < 0:
            return ["color: red" if positive_good else "color: green"]
        else:
            return [""]


    styled = result.style.apply(
        lambda row: color_delta_row(row, result),
        axis=1,
        subset=["Δ"]
    )

    st.dataframe(styled, use_container_width=True)
    # ==================================================
    # TOTAL TABLE (FULL P&L)
    # ==================================================
    st.subheader("Total Values (No Unit)")

    totals = []

    

    # SCENARIO değerleri al
    def get_val(scenario, col):
        if scenario in df_group.index:
            return df_group.loc[scenario, col]
        return 0

    act_units = get_val("MARCH", "units")
    bdg_units = get_val("BDG", "units")

    act_tn = get_val("MARCH", "tn")
    bdg_tn = get_val("BDG", "tn")

    act_cogs = get_val("MARCH", "cogs")
    bdg_cogs = get_val("BDG", "cogs")

    act_agm = get_val("MARCH", "agm")
    bdg_agm = get_val("BDG", "agm")

    act_vce = get_val("MARCH", "vce")
    bdg_vce = get_val("BDG", "vce")


   
    # ✅ VAR (P&L den türet)
    act_var = act_tn - act_cogs - act_vce - act_agm
    bdg_var = bdg_tn - bdg_cogs - bdg_vce - bdg_agm

    # ✅ SGM
    act_sgm = act_agm + act_var
    bdg_sgm = bdg_agm + bdg_var

    # ✅ Build rows (SENİN İSTEDİĞİN SIRA)
    rows = [
        ("UNITS", act_units, bdg_units),
        ("TN", act_tn, bdg_tn),
        ("COGS", act_cogs, bdg_cogs),
        ("VCE", act_vce, bdg_vce),
        ("AGM", act_agm, bdg_agm),
        ("SGM", act_sgm, bdg_sgm),
    ]

    for name, act_val, bdg_val in rows:
        totals.append({
            "Metric": name,
            "ACT": act_val,
            "BDG": bdg_val,
            "Δ": act_val - bdg_val
        })

    totals_df = pd.DataFrame(totals)
    totals_styled = totals_df.style.apply(
        lambda row: color_delta_row(row, totals_df),
        axis=1,
        subset=["Δ"]
    )

    st.dataframe(
        totals_styled,
        use_container_width=True
    )
    st.caption("Δ = ACT - BDG")