
import streamlit as st
import pandas as pd
from pathlib import Path

# ==================================================
# CONFIG
# ==================================================
BASE_PATH = Path(r"C:\Users\v47012b\OneDrive - Iveco Group\Documenti\volpe_analysis\data\raw")


# ==================================================
# CLEAN COLUMN NAMES
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
def load_all():

    # ACT
    act = pd.read_excel(BASE_PATH / "raw_agm03.xlsx")
    act = clean_columns(act)

    act = act.rename(columns={
        "CUSTOMER MERGE": "customer",
        "PRODUCT": "product",
        "PN ALLESTIMENTO": "pn",
        "ACT UNITS": "units",
        "ACT TN": "tn",
        "ACT COGS": "cogs",
        "ACT AGM": "agm",
        "ACT SGM": "sgm"
    })
    act["scenario"] = "MARCH"

    # BDG
    bdg = pd.read_excel(BASE_PATH / "raw_bdg26.xlsx")
    bdg = clean_columns(bdg)

    bdg = bdg.rename(columns={
        "CUSTOMER MERGE": "customer",
        "PRODUCT": "product",
        "PN ALLESTIMENTO": "pn",
        "UNITS": "units",
        "TN": "tn",
        "COGS": "cogs",
        "AGM": "agm",
        "SGM": "sgm"
    })
    bdg["scenario"] = "BDG26"

    # FCST
    fcst = pd.read_excel(BASE_PATH / "raw_fcs1_26.xlsx")
    fcst = clean_columns(fcst)

    fcst = fcst.rename(columns={
        "CUSTOMER MERGE": "customer",
        "PRODUCT": "product",
        "PN ALLESTIMENTO": "pn",
        "FY UNITS": "units",
        "FY TN": "tn",
        "FY COGS": "cogs",
        "AGM": "agm",
        "SGM": "sgm"
    })
    fcst["scenario"] = "FCST1"

    # MERGE ALL
    df = pd.concat([act, bdg, fcst])

    # NUMERIC CLEAN
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

    st.divider()

    # ==================================================
    # FILTERS
    # ==================================================
    customers = st.multiselect(
        "Customer",
        sorted(df["customer"].dropna().unique())
    )

    if not customers:
        st.info("Please select customer")
        st.stop()

    df = df[df["customer"].isin(customers)]

    group_cols = st.multiselect(
        "Group By",
        ["customer", "product", "pn"],
        default=["customer", "product"]
    )

    if not group_cols:
        group_cols = ["customer"]

    # ==================================================
    # STEP 1 - AGGREGATE FIRST ✅
    # ==================================================
    df_group = df.groupby(
        group_cols + ["scenario"],
        as_index=False
    ).agg({
        "units": "sum",
        "tn": "sum",
        "cogs": "sum",
        "agm": "sum",
        "sgm": "sum"
    })

    # ==================================================
    # STEP 2 - CALCULATE % ✅ (CORRECT PLACE)
    # ==================================================
    df_group["AGM%"] = df_group["agm"] / df_group["tn"]
    df_group["SGM%"] = df_group["sgm"] / df_group["tn"]

    df_group = df_group.replace([float("inf"), -float("inf")], 0).fillna(0)

    # ==================================================
    # STEP 3 - PIVOT ✅
    # ==================================================
    pivot = df_group.pivot(
    index=group_cols,
    columns="scenario"
)

    pivot.columns = [f"{c[1]}_{c[0].upper()}" for c in pivot.columns]
    pivot = pivot.reset_index()

    full = pivot.copy()


    
    # ✅ FINAL TRUE %
    full["MARCH_AGM%"] = (full["MARCH_AGM"] / full["MARCH_TN"]) * 100
    full["MARCH_SGM%"] = (full["MARCH_SGM"] / full["MARCH_TN"]) * 100

    full["BDG26_AGM%"] = (full["BDG26_AGM"] / full["BDG26_TN"]) * 100
    full["BDG26_SGM%"] = (full["BDG26_SGM"] / full["BDG26_TN"]) * 100

    full["FCST1_AGM%"] = (full["FCST1_AGM"] / full["FCST1_TN"]) * 100
    full["FCST1_SGM%"] = (full["FCST1_SGM"] / full["FCST1_TN"]) * 100

    # ✅ PRICE / COST

    full["MARCH_PRICE"] = full["MARCH_TN"] / full["MARCH_UNITS"]
    full["MARCH_COST"]  = full["MARCH_COGS"] / full["MARCH_UNITS"]

    full["BDG26_PRICE"] = full["BDG26_TN"] / full["BDG26_UNITS"]
    full["BDG26_COST"]  = full["BDG26_COGS"] / full["BDG26_UNITS"]

    full["FCST1_PRICE"] = full["FCST1_TN"] / full["FCST1_UNITS"]
    full["FCST1_COST"]  = full["FCST1_COGS"] / full["FCST1_UNITS"]
    

    # ==================================================
    # KPI EXTRA
    # ==================================================
    full["VAR_UNITS"] = full["MARCH_UNITS"] - full["BDG26_UNITS"]
    full["VAR_TN"] = full["MARCH_TN"] - full["BDG26_TN"]

    full["DELTA_AGM%"] = full["MARCH_AGM%"] - full["BDG26_AGM%"]
    full["DELTA_SGM%"] = full["MARCH_SGM%"] - full["BDG26_SGM%"]

    full = full.replace([float("inf"), -float("inf")], 0).fillna(0)

    # ==================================================
# PERFORMANCE COMMENT (AGM vs SGM)
# ==================================================
    # ==================================================
# PERFORMANCE COMMENT (SAFE VERSION)
# ==================================================
    def performance_comment(row):

        tn = row.get("MARCH_TN", 0)
        agm = row.get("MARCH_AGM", 0)
        sgm = row.get("MARCH_SGM", 0)

        label = ""
        if row.get("customer") == "TOTAL":
            label = "TOTAL → "

        if tn == 0:
            return f"{label}No sales"

        diff = agm - sgm
        margin = (agm / tn) * 100 if tn != 0 else 0

        if diff > 0:
            return f"{label}AGM > SGM (+{diff:,.0f}) | Margin {margin:.1f}%"

        if diff < 0:
            return f"{label}AGM < SGM ({diff:,.0f}) | Margin {margin:.1f}%"

        return f"{label}On target | Margin {margin:.1f}%"

    # ✅ ÇOK KRİTİK → BUNU EKLE
    full["INSIGHT"] = full.apply(performance_comment, axis=1)



    # ==================================================
    # SELECT METRICS
    # ==================================================
    all_metrics = [c for c in full.columns if c not in group_cols]

    selected_metrics = st.multiselect(
        "Select Metrics",
        all_metrics,
        default=["MARCH_TN", "MARCH_AGM", "MARCH_AGM%"]
    )
    # ✅ dependency auto-add

    def add_dependencies(selected):
        needed = set(selected)

        mapping = {
            # ✅ %
            "MARCH_AGM%": ["MARCH_AGM", "MARCH_TN"],
            "MARCH_SGM%": ["MARCH_SGM", "MARCH_TN"],
            "BDG26_AGM%": ["BDG26_AGM", "BDG26_TN"],
            "BDG26_SGM%": ["BDG26_SGM", "BDG26_TN"],
            "FCST1_AGM%": ["FCST1_AGM", "FCST1_TN"],
            "FCST1_SGM%": ["FCST1_SGM", "FCST1_TN"],

            # ✅ PRICE
            "MARCH_PRICE": ["MARCH_TN", "MARCH_UNITS"],
            "BDG26_PRICE": ["BDG26_TN", "BDG26_UNITS"],
            "FCST1_PRICE": ["FCST1_TN", "FCST1_UNITS"],

            # ✅ COST
            "MARCH_COST": ["MARCH_COGS", "MARCH_UNITS"],
            "BDG26_COST": ["BDG26_COGS", "BDG26_UNITS"],
            "FCST1_COST": ["FCST1_COGS", "FCST1_UNITS"],
        }

        for metric in selected:
            if metric in mapping:
                needed.update(mapping[metric])

        return list(needed)


    selected_metrics = add_dependencies(selected_metrics)
   
    view_df = full[group_cols + selected_metrics + ["INSIGHT"]].copy()
    display_cols = selected_metrics.copy()
    # sadece % göster
    display_cols = [c for c in display_cols if not c.endswith("_AGM") and not c.endswith("_TN")]

   



    # ==================================================
    # TOTAL ROW ✅
    # ==================================================
  

    # -------- TOTAL --------
    total = full.select_dtypes(include="number").sum()

    def safe_ratio(num, den, target):
        if num in total and den in total:
            total[target] = (total[num] / total[den]) * 100

    # ✅ tüm % hesap
    safe_ratio("MARCH_AGM", "MARCH_TN", "MARCH_AGM%")
    safe_ratio("MARCH_SGM", "MARCH_TN", "MARCH_SGM%")

    safe_ratio("BDG26_AGM", "BDG26_TN", "BDG26_AGM%")
    safe_ratio("BDG26_SGM", "BDG26_TN", "BDG26_SGM%")

    safe_ratio("FCST1_AGM", "FCST1_TN", "FCST1_AGM%")
    safe_ratio("FCST1_SGM", "FCST1_TN", "FCST1_SGM%")

    def safe_unit(num, den, target):
        if num in total and den in total:
            total[target] = total[num] / total[den]

    # ✅ MARCH
    safe_unit("MARCH_TN", "MARCH_UNITS", "MARCH_PRICE")
    safe_unit("MARCH_COGS", "MARCH_UNITS", "MARCH_COST")

    # ✅ BDG
    safe_unit("BDG26_TN", "BDG26_UNITS", "BDG26_PRICE")
    safe_unit("BDG26_COGS", "BDG26_UNITS", "BDG26_COST")

    # ✅ FCST
    safe_unit("FCST1_TN", "FCST1_UNITS", "FCST1_PRICE")
    safe_unit("FCST1_COGS", "FCST1_UNITS", "FCST1_COST")


    # TOTAL DF oluştur
    total_df = pd.DataFrame([total])

    # group kolonları ekle
    for col in group_cols:
        total_df[col] = "TOTAL"

    # ✅ insight (FULL data ile)
    total_df["INSIGHT"] = total_df.apply(performance_comment, axis=1)

    # ✅ sonra view_df kolonlarına hizala
    total_df = total_df.reindex(columns=view_df.columns, fill_value="")

    # ✅ concat
    view_df = pd.concat([view_df, total_df], ignore_index=True)


    # ==================================================
    # FORMAT ✅
    # ==================================================
    column_config = {}
    column_config["INSIGHT"] = st.column_config.TextColumn("Insight")
    for col in view_df.columns:

        if col in group_cols:
            column_config[col] = st.column_config.TextColumn(col)

        elif col.endswith("%"):
            column_config[col] = st.column_config.NumberColumn(
                col, format="%.1f %%"
            )

        elif "TN" in col:
            column_config[col] = st.column_config.NumberColumn(
                col, format="€ %.0f"
            )

        elif "UNITS" in col:
            column_config[col] = st.column_config.NumberColumn(
                col, format="%.0f"
            )
        elif "PRICE" in col or "COST" in col:
            column_config[col] = st.column_config.NumberColumn(
                col, format="€ %.1f"
            )

        else:
            column_config[col] = st.column_config.NumberColumn(col)

    # ==================================================
    # OUTPUT ✅
    # ==================================================
    st.dataframe(
        view_df,
        use_container_width=True,
        height=550,
        column_config=column_config
    )