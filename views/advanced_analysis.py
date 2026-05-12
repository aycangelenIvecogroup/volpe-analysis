import streamlit as st
import pandas as pd
from pathlib import Path

# ==================================================
# CONFIG
# ==================================================
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
# LOAD
# ==================================================
@st.cache_data
def load_all():

    def load_file(path, scenario, mapping):
        df = pd.read_excel(path)
        df = clean_columns(df)

        df = df.rename(columns=mapping)
        df["SCENARIO"] = scenario

        return df

    act = load_file(
        BASE_PATH / "raw_agm03.xlsx",
        "MARCH",
        {
            "CUSTOMER MERGE": "customer",
            "PRODUCT": "product",
            "PN ALLESTIMENTO": "pn",
            "ACT UNITS": "units",
            "ACT TN": "tn",
            "ACT COGS": "cogs",
            "ACT AGM": "agm",
            "ACT SGM": "sgm"
        }
    )

    bdg = load_file(
        BASE_PATH / "raw_bdg26.xlsx",
        "BDG26",
        {
            "CUSTOMER MERGE": "customer",
            "PRODUCT": "product",
            "PN ALLESTIMENTO": "pn",
            "UNITS": "units",
            "TN": "tn",
            "COGS": "cogs",
            "AGM": "agm",
            "SGM": "sgm"
        }
    )

    fcst = load_file(
        BASE_PATH / "raw_fcs1_26.xlsx",
        "FCST1",
        {
            "CUSTOMER MERGE": "customer",
            "PRODUCT": "product",
            "PN ALLESTIMENTO": "pn",
            "FY UNITS": "units",
            "FY TN": "tn",
            "FY COGS": "cogs",
            "AGM": "agm",
            "SGM": "sgm"
        }
    )

    df = pd.concat([act, bdg, fcst], ignore_index=True)

    for c in ["units", "tn", "cogs", "agm", "sgm"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    return df

# ==================================================
# MAIN PAGE
# ==================================================
def render_advanced_analysis():

    st.title("🔥 Advanced Analysis")
    st.caption("Correct KPI engine (AGM / TN)")

    df = load_all()

    # ======================
    # FILTER
    # ======================
    customers = st.multiselect(
        "Customer",
        sorted(df["customer"].dropna().unique())
    )

    if not customers:
        st.info("Select customer")
        st.stop()

    df = df[df["customer"].isin(customers)]

    group_cols = st.multiselect(
        "Group By",
        ["customer", "product", "pn"],
        default=["customer", "product"]
    )

    if not group_cols:
        group_cols = ["customer"]

    # ======================
    # AGGREGATE
    # ======================
    df_group = df.groupby(group_cols + ["SCENARIO"], as_index=False).agg({
        "units": "sum",
        "tn": "sum",
        "cogs": "sum",
        "agm": "sum",
        "sgm": "sum"
    })

    # ======================
    # SAFE KPI
    # ======================
    df_group["AGM%"] = df_group["agm"] / df_group["tn"].replace(0, 1)
    df_group["SGM%"] = df_group["sgm"] / df_group["tn"].replace(0, 1)

    # ======================
    # ✅ FIXED PIVOT (ÖNEMLİ)
    # ======================
    pivot = df_group.pivot_table(
        index=group_cols,
        columns="SCENARIO",
        values=["units", "tn", "cogs", "agm", "sgm"],
        aggfunc="sum"
    )

    pivot.columns = [f"{col[1]}_{col[0].upper()}" for col in pivot.columns]
    pivot = pivot.reset_index()

    full = pivot.copy().fillna(0)

    # ======================
    # KPI CALC
    # ======================
    def safe_pct(num, den):
        return (num / den.replace(0, 1)) * 100

    # % KPI
    for scen in ["MARCH", "BDG26", "FCST1"]:
        if f"{scen}_TN" in full.columns:
            full[f"{scen}_AGM%"] = safe_pct(full[f"{scen}_AGM"], full[f"{scen}_TN"])
            full[f"{scen}_SGM%"] = safe_pct(full[f"{scen}_SGM"], full[f"{scen}_TN"])

            full[f"{scen}_PRICE"] = full[f"{scen}_TN"] / full[f"{scen}_UNITS"].replace(0, 1)
            full[f"{scen}_COST"] = full[f"{scen}_COGS"] / full[f"{scen}_UNITS"].replace(0, 1)

    # ======================
    # VARIANCE
    # ======================
    if "MARCH_TN" in full and "BDG26_TN" in full:
        full["VAR_TN"] = full["MARCH_TN"] - full["BDG26_TN"]
        full["VAR_UNITS"] = full["MARCH_UNITS"] - full["BDG26_UNITS"]

        full["Δ AGM%"] = full["MARCH_AGM%"] - full["BDG26_AGM%"]
        full["Δ SGM%"] = full["MARCH_SGM%"] - full["BDG26_SGM%"]

    # ======================
    # INSIGHT ENGINE
    # ======================
    def performance_comment(row):

        tn = row.get("MARCH_TN", 0)
        agm = row.get("MARCH_AGM", 0)
        sgm = row.get("MARCH_SGM", 0)

        if tn == 0:
            return "No sales"

        diff = agm - sgm
        margin = (agm / tn) * 100

        if diff > 0:
            return f"AGM > SGM (+{diff:,.0f}) | margin {margin:.1f}%"

        if diff < 0:
            return f"AGM < SGM ({diff:,.0f}) | margin {margin:.1f}%"

        return f"On target | margin {margin:.1f}%"

    full["INSIGHT"] = full.apply(performance_comment, axis=1)

    # ======================
    # SELECT METRIC
    # ======================
    all_metrics = [c for c in full.columns if c not in group_cols]

    selected_metrics = st.multiselect(
        "Select Metrics",
        all_metrics,
        default=["MARCH_TN", "MARCH_AGM", "MARCH_AGM%"]
    )

    # ✅ INSIGHT'ı filtrele (duplicate olmasın)
    selected_metrics = [m for m in selected_metrics if m != "INSIGHT"]

    # ✅ duplicate-safe column list
    cols = list(dict.fromkeys(group_cols + selected_metrics + ["INSIGHT"]))

    view_df = full[cols].copy()

    # ✅ ekstra güvenlik
    view_df = view_df.loc[:, ~view_df.columns.duplicated()]

   
    

    # ======================
    # TOTAL ROW
    # ======================
    total = full.select_dtypes(include="number").sum()

    def safe_ratio(num, den, name):
        if num in total and den in total:
            total[name] = (total[num] / total[den]) * 100

    safe_ratio("MARCH_AGM", "MARCH_TN", "MARCH_AGM%")
    safe_ratio("BDG26_AGM", "BDG26_TN", "BDG26_AGM%")

    total_df = pd.DataFrame([total])

    for col in group_cols:
        total_df[col] = "TOTAL"

    total_df["INSIGHT"] = total_df.apply(performance_comment, axis=1)

    total_df = total_df.reindex(columns=view_df.columns, fill_value="")
    view_df = pd.concat([view_df, total_df], ignore_index=True)

    # ======================
    # OUTPUT
    # ======================
    st.dataframe(view_df, use_container_width=True, height=600)