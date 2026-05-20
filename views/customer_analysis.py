import streamlit as st
import pandas as pd
import numpy as np

from pathlib import Path

BASE_PATH = Path(__file__).resolve().parents[1] / "data" / "raw"


# =========================
# LOAD & CLEAN
# =========================
def clean_columns(df):
    df.columns = (
        df.columns.astype(str)
        .str.replace("\n", " ")
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
        .str.upper()
    )
    return df


@st.cache_data
def load_data():

    # ================= ACTUAL
    act = pd.read_excel(BASE_PATH / "product_raw_db_c03.xlsx", sheet_name="Table1")
    act = clean_columns(act)

    act = act.rename(columns={
        "CUSTOMER MERGE": "customer",
        "FAMILY": "family",
        "PN": "pn",
        "ACT UNITS": "actual_unit",
        "ACT TN": "actual_tn",
        "ACT COGS": "actual_cogs",
        "ACT VCE": "actual_vce",
        "ACT AGM": "actual_agm",
        "ACT SGM": "actual_sgm",
        "PRODUCT": "product",
    })
    
    if "PN ALLESTIMENTO" in act.columns:
        act["pn"] = act["PN ALLESTIMENTO"]
    elif "PN" in act.columns:
        act["pn"] = act["PN"]


    # ================= BDG
    bdg = pd.read_excel(BASE_PATH / "product_raw_db_bdg26.xlsx", sheet_name="Table2")
    bdg = clean_columns(bdg)

    bdg = bdg.rename(columns={
        "CUSTOMER MERGE": "customer",
        "FAMILY": "family",
        "PN": "pn",
        "UNITS": "bdg26_unit",
        "TN": "bdg26_tn",
        "COGS": "bdg26_cogs",
        "VCE": "bdg26_vce",
        "AGM": "bdg26_agm",
        "SGM": "bdg26_sgm",
        "PRODUCT": "product",
    })

    if "PN ALLESTIMENTO" in act.columns:
        act["pn"] = act["PN ALLESTIMENTO"]
    elif "PN" in act.columns:
        act["pn"] = act["PN"]

    # ================= LY
    ly = pd.read_excel(BASE_PATH / "product_raw_db_c12_2025.xlsx", sheet_name="Table1")
    ly = clean_columns(ly)

    ly = ly.rename(columns={
        "CUSTOMER MERGE": "customer",
        "FAMILY": "family",
        "PN": "pn",
        "ACT UNITS": "ly25_unit",
        "ACT TN": "ly25_tn",
        "ACT COGS": "ly25_cogs",
        "ACT VCE": "ly25_vce",
        "ACT AGM": "ly25_agm",
        "ACT SGM": "ly25_sgm",
        "PRODUCT": "product",
    })
    
    if "PN ALLESTIMENTO" in act.columns:
        act["pn"] = act["PN ALLESTIMENTO"]
    elif "PN" in act.columns:
        act["pn"] = act["PN"]


        # ================= FCS1
    fcs = pd.read_excel(BASE_PATH / "raw_fcs1_26.xlsx")
    fcs = clean_columns(fcs)

    fcs = fcs.rename(columns={
        "CUSTOMER MERGE": "customer",
        "FAMILY": "family",
        "PN": "pn",
        "FY UNITS": "fcs1_unit",
        "FY TN": "fcs1_tn",
        "FY COGS": "fcs1_cogs",
        "FY VCE": "fcs1_vce",
        "AGM": "fcs1_agm",
        "SGM": "fcs1_sgm",
        "PRODUCT": "product",
    })
    
    # =========================
    # CLEAN ALL DATAFRAMES ✅
    # =========================

    dfs = [act, bdg, ly, fcs]

    # numeric columns
    num_cols = [
        "actual_unit","actual_tn","actual_cogs","actual_vce","actual_agm","actual_sgm",
        "bdg26_unit","bdg26_tn","bdg26_cogs","bdg26_vce","bdg26_agm","bdg26_sgm",
        "fcs1_unit","fcs1_tn","fcs1_cogs","fcs1_vce","fcs1_agm","fcs1_sgm",
        "ly25_unit","ly25_tn","ly25_cogs","ly25_vce","ly25_agm","ly25_sgm"
    ]

    for d in dfs:

        # ✅ PN güvenli oluştur
        if "PN ALLESTIMENTO" in d.columns:
            d["pn"] = d["PN ALLESTIMENTO"]
        elif "PN" in d.columns:
            d["pn"] = d["PN"]
        else:
            d["pn"] = "NO_PN"

        if "family" not in d.columns:
            d["family"] = "NO_FAMILY"

        if "product" not in d.columns:
            d["product"] = "NO_PRODUCT"

        # ✅ string fix
        d["pn"] = d["pn"].astype(str).str.strip()
        d["family"] = d["family"].astype(str).str.strip()
        d["product"] = d["product"].astype(str).str.strip()

        d["pn"] = d["pn"].replace("nan","NO_PN")
        d["family"] = d["family"].replace("nan","NO_FAMILY")

        # ✅ numeric fix
        for c in num_cols:
            if c in d.columns:
                d[c] = pd.to_numeric(d[c], errors="coerce")

    # =========================
    # GROUP
    # =========================
    group_cols = ["customer","family","product","pn"]

    act = act.groupby(group_cols, as_index=False).sum(numeric_only=True)
    bdg = bdg.groupby(group_cols, as_index=False).sum(numeric_only=True)
    fcs = fcs.groupby(group_cols, as_index=False).sum(numeric_only=True)
    ly  = ly.groupby(group_cols, as_index=False).sum(numeric_only=True)

    # ================= MERGE
    merge_keys = ["customer","family","pn","product"]
    df = act.merge(bdg, on=merge_keys, how="outer")
    df = df.merge(fcs, on=merge_keys, how="outer")
    df = df.merge(ly, on=merge_keys, how="outer")

    df = df.fillna(0)

    return df


# =========================
# CALCULATIONS
# =========================
def compute_metrics(df):

    # percentages
    for s in ["actual", "bdg26", "fcs1", "ly25"]:
        if f"{s}_agm" in df.columns and f"{s}_tn" in df.columns:
            df[f"{s}_agm_pct"] = df[f"{s}_agm"] / df[f"{s}_tn"].replace(0, np.nan)
        else:
            df[f"{s}_agm_pct"] = np.nan

        if f"{s}_sgm" in df.columns and f"{s}_tn" in df.columns:
            df[f"{s}_sgm_pct"] = df[f"{s}_sgm"] / df[f"{s}_tn"].replace(0, np.nan)
        else:
            df[f"{s}_sgm_pct"] = np.nan

    # Δ absolute
    scenarios = ["bdg26", "fcs1", "ly25"]

    for s in scenarios:
        df[f"delta_agm_{s}"] = df[f"{s}_agm"] - df["actual_agm"]
        df[f"delta_sgm_{s}"] = df[f"{s}_sgm"] - df["actual_sgm"]
        df[f"delta_tn_{s}"]  = df[f"{s}_tn"] - df["actual_tn"]

        # Δ %
        df[f"delta_agm_pct_{s}"] = df[f"{s}_agm_pct"] - df["actual_agm_pct"]
        df[f"delta_sgm_pct_{s}"] = df[f"{s}_sgm_pct"] - df["actual_sgm_pct"]
        

    return df


# =========================
# FORMAT
# =========================

def fmt_num(x):
    try:
        if pd.isna(x):
            return ""
        return f"{float(x):,.0f}"   # ✅ thousand separator
    except:
        return x



def fmt_pct(x):
    try:
        if pd.isna(x):
            return ""
        return f"{float(x)*100:.1f}%"
    except:
        return x


def fmt_pp(x):
    try:
        if pd.isna(x):
            return ""
        return f"{float(x)*100:.1f} pp"
    except:
        return x


# =========================
# UI
# =========================
def render_customer_analysis():
    st.title("📊 Customer Product Analysis")

    df = load_data()
    df = compute_metrics(df)

    # filter customer
    
    customers = st.multiselect(
        "Select Customer(s)",
        sorted(df["customer"].dropna().unique()),
        default=[]  # boş başlasın
    )

    if customers:
        df = df[df["customer"].isin(customers)]

    
    families = st.multiselect(
        "Select Family",
        sorted(df["family"].dropna().unique())
    )

    if families:
        df = df[df["family"].isin(families)]

    pns = st.multiselect(
        "Select PN",
        sorted(df["pn"].dropna().unique())
    )

    if pns:
        df = df[df["pn"].isin(pns)]

    
    products = st.multiselect(
        "Select Product",
        sorted(df["product"].dropna().unique())
    )

    if products:
        df = df[df["product"].isin(products)]
    df_display = df.copy()
   

    
    # =========================
    # DEFAULT VIEW LOGIC
    # =========================
    no_detail = not families and not products and not pns

    
    if no_detail:
        df_display = df.groupby("customer", as_index=False).sum(numeric_only=True)

        # ✅ eksik kolonları geri ekle
        df_display["family"] = "-"
        df_display["product"] = "-"
        df_display["pn"] = "-"


    # =========================
    # SELECTORS
    # =========================

    actual_sel = st.multiselect("Actual Month", [
        "actual_unit","actual_tn","actual_agm","actual_cogs","actual_vce","actual_sgm"
    ])

    bdg_sel = st.multiselect("Budget2026", [
        "bdg26_unit","bdg26_tn","bdg26_agm","bdg26_cogs","bdg26_vce","bdg26_sgm"
    ])

    fcs_sel = st.multiselect("Forecast1", [
        "fcs1_unit","fcs1_tn","fcs1_agm","fcs1_cogs","fcs1_vce","fcs1_sgm"
    ])

    ly_sel = st.multiselect("LY2025", [
        "ly25_unit","ly25_tn","ly25_agm","ly25_cogs","ly25_vce","ly25_sgm"
    ])

    pct_sel = st.multiselect("Percentages", [
        "actual_agm_pct","bdg26_agm_pct","fcs1_agm_pct","ly25_agm_pct",
        "actual_sgm_pct","bdg26_sgm_pct","fcs1_sgm_pct","ly25_sgm_pct"
    ])

    ops_sel = st.multiselect("Operations", [
        "delta_agm_bdg26","delta_agm_fcs1","delta_agm_ly25",
        "delta_agm_pct_bdg26","delta_agm_pct_fcs1","delta_agm_pct_ly25",
        "delta_sgm_bdg26","delta_sgm_fcs1","delta_sgm_ly25",
        "delta_sgm_pct_bdg26","delta_sgm_pct_fcs1","delta_sgm_pct_ly25",
        "delta_tn_bdg26","delta_tn_fcs1","delta_tn_ly25",
    ])
    # =========================
    # DEFAULT SELECTION
    # =========================
    
    if not (actual_sel or bdg_sel or fcs_sel or ly_sel):
        st.info("Select at least one metric (TN / AGM) to see meaningful results")


    # =========================
    # BUILD COLUMNS
    # =========================
    
    columns = ["customer","family","product","pn"]
    columns += actual_sel + bdg_sel + fcs_sel + ly_sel + ops_sel

    # ✅ pct sadece user seçerse
    if pct_sel:
        columns += pct_sel



    out = df_display.reindex(columns=columns, fill_value="").copy()
    
    # =========================
    # TOTAL ROW (SMART)
    # =========================
    total_row = {}
    raw_totals = {}

    for col in out.columns:
        if col in ["customer","family","product","pn"]:
            total_row[col] = "TOTAL"
        elif "pct" not in col:
            val = pd.to_numeric(out[col], errors="coerce").sum()
            raw_totals[col] = val
            total_row[col] = val
        else:
            total_row[col] = None

    def safe_div(a, b):
        return a / b if b not in [0, None, np.nan] else 0

    # ✅ AGM %
       
    # ✅ ALWAYS compute percentages from base data (df_display)

    if df_display["actual_tn"].sum() != 0:
        total_row["actual_agm_pct"] = (
            df_display["actual_agm"].sum() /
            df_display["actual_tn"].sum()
        )

    if df_display["bdg26_tn"].sum() != 0:
        total_row["bdg26_agm_pct"] = (
            df_display["bdg26_agm"].sum() /
            df_display["bdg26_tn"].sum()
        )

    if df_display["fcs1_tn"].sum() != 0:
        total_row["fcs1_agm_pct"] = (
            df_display["fcs1_agm"].sum() /
            df_display["fcs1_tn"].sum()
        )

    if df_display["ly25_tn"].sum() != 0:
        total_row["ly25_agm_pct"] = (
            df_display["ly25_agm"].sum() /
            df_display["ly25_tn"].sum()
        )




    if df_display["actual_tn"].sum() != 0:
        total_row["actual_sgm_pct"] = (
            df_display["actual_sgm"].sum() /
            df_display["actual_tn"].sum()
        )

    if df_display["bdg26_tn"].sum() != 0:
        total_row["bdg26_sgm_pct"] = (
            df_display["bdg26_sgm"].sum() /
            df_display["bdg26_tn"].sum()
        )

    if df_display["fcs1_tn"].sum() != 0:
        total_row["fcs1_sgm_pct"] = (
            df_display["fcs1_sgm"].sum() /
            df_display["fcs1_tn"].sum()
        )

    if df_display["ly25_tn"].sum() != 0:
        total_row["ly25_sgm_pct"] = (
            df_display["ly25_sgm"].sum() /
            df_display["ly25_tn"].sum()
        )
    

    out = pd.concat([out, pd.DataFrame([total_row])], ignore_index=True)


    # =========================
    # FORMAT APPLY
    # =========================
    for col in out.columns:

        if "pct" in col:
            if "delta" in col:
                out[col] = out[col].apply(fmt_pp)
            else:
                out[col] = out[col].apply(fmt_pct)

        elif "delta" in col:
            out[col] = out[col].apply(fmt_num)

        elif col not in ["customer","family","pn"]:
            out[col] = out[col].apply(fmt_num)

    # =========================
    # OUTPUT
    # =========================
    st.dataframe(out, use_container_width=True)