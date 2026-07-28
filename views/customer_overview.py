import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

BASE_PATH = Path("data/clean excel files")  # Adjust the path as needed

# ======================
# LOAD ✅ (DOĞRU STRUCTURE)
# ======================
@st.cache_data
def load_data():

    def clean_cols(df):
        df.columns = (
            df.columns.astype(str)
            .str.replace("\n", " ")
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
            .str.upper()
        )
        return df


    def fix_customer(df):

        df["customer"] = (
            df["customer"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        customer_mapping = {
            "SDF": "SAME DEUTZ-FAHR DEUTSCHLAND GMBH",
            "ATLAS COPCO_NC": "ATLAS COPCO",
            "YANMAR ITALY": "YANMAR"
        }

        df["customer"] = df["customer"].replace(customer_mapping)

        return df

    act = pd.read_excel(BASE_PATH / "c06_2026_clean.xlsx")
    act = clean_cols(act)

    act = act.rename(columns={
        "CUSTOMER MERGE": "customer",
        "ACCOUNTABILITY 4": "acc4",
        "ACCOUNTABILITY 5": "acc5",
        "UNITS": "units",
        "TN": "tn",
        "AGM": "agm",
        "SGM": "sgm"
    })[
        [
            "customer",
            "acc4",
            "acc5",
            "units",
            "tn",
            "agm",
            "sgm"
        ]
    ]

    act = fix_customer(act)

    act["tn"] = pd.to_numeric(act["tn"], errors="coerce")
    act["agm"] = pd.to_numeric(act["agm"], errors="coerce")
    act["sgm"] = pd.to_numeric(act["sgm"], errors="coerce")
    act["units"] = pd.to_numeric(act["units"], errors="coerce")

    act = act.fillna(0)
    customer_attributes = (
        act[
            ["customer", "acc4", "acc5"]
        ]
        .drop_duplicates(subset=["customer"])
    )


    act = act.groupby("customer", as_index=False)[["units", "tn", "agm", "sgm"]].sum()

    act["SCENARIO"] = "ACT"

   
    # === BDG ===
    bdg = pd.read_excel(BASE_PATH / "BDG2026_v4_clean.xlsx")
    bdg = clean_cols(bdg)

    bdg = bdg.rename(columns={
        "CUSTOMER MERGE": "customer",
        "ACCOUNTABILITY 4": "acc4",
        "ACCOUNTABILITY 5": "acc5",
        "UNITS": "units",
        "TN": "tn",
        "AGM": "agm",
        "SGM": "sgm"
    })[
        [
            "customer",
            "acc4",
            "acc5",
            "units",
            "tn",
            "agm",
            "sgm"
        ]
    ]


    bdg = fix_customer(bdg)

    bdg["tn"] = pd.to_numeric(bdg["tn"], errors="coerce")
    bdg["agm"] = pd.to_numeric(bdg["agm"], errors="coerce")
    bdg["sgm"] = pd.to_numeric(bdg["sgm"], errors="coerce")
    bdg["units"] = pd.to_numeric(bdg["units"], errors="coerce")

    bdg = bdg.fillna(0)

    bdg = bdg.groupby("customer", as_index=False)[["units", "tn", "agm", "sgm"]].sum()

    bdg["SCENARIO"] = "BDG"

    # === LY ===
    ly = pd.read_excel(BASE_PATH / "LY25_clean.xlsx")
    ly = clean_cols(ly)

    ly = ly.rename(columns={
        "CUSTOMER MERGE": "customer",
        "ACCOUNTABILITY 4": "acc4",
        "ACCOUNTABILITY 5": "acc5",
        "UNITS": "units",
        "TN": "tn",
        "AGM": "agm",
        "SGM": "sgm"
    })[
        [
            "customer",
            "acc4",
            "acc5",
            "units",
            "tn",
            "agm",
            "sgm"
        ]
    ]

    ly = fix_customer(ly)

    ly["tn"] = pd.to_numeric(ly["tn"], errors="coerce")
    ly["agm"] = pd.to_numeric(ly["agm"], errors="coerce")
    ly["sgm"] = pd.to_numeric(ly["sgm"], errors="coerce")
    ly["units"] = pd.to_numeric(ly["units"], errors="coerce")

    ly = ly.fillna(0)

    ly = ly.groupby("customer", as_index=False)[["units", "tn", "agm", "sgm"]].sum()

    ly["SCENARIO"] = "LY"

    fcs = pd.read_excel(BASE_PATH / "fcst1_2026_clean.xlsx")
    fcs = clean_cols(fcs)

    fcs = fcs.rename(columns={
       "CUSTOMER MERGE": "customer",
        "ACCOUNTABILITY 4": "acc4",
        "ACCOUNTABILITY 5": "acc5",
        "UNITS": "units",
        "TN": "tn",
        "AGM": "agm",
        "SGM": "sgm"
    })[
        [
            "customer",
            "acc4",
            "acc5",
            "units",
            "tn",
            "agm",
            "sgm"
        ]
    ]


    fcs = fix_customer(fcs)

    fcs["tn"] = pd.to_numeric(fcs["tn"], errors="coerce")
    fcs["agm"] = pd.to_numeric(fcs["agm"], errors="coerce")
    fcs["sgm"] = pd.to_numeric(fcs["sgm"], errors="coerce")
    fcs["units"] = pd.to_numeric(fcs["units"], errors="coerce")

    fcs = fcs.fillna(0)

    fcs = fcs.groupby("customer", as_index=False)[["units", "tn", "agm", "sgm"]].sum()

    fcs["SCENARIO"] = "FCS1"

    # === PM (Previous Month) ===
    pm = pd.read_excel(BASE_PATH / "c05_2026_clean.xlsx")
    pm = clean_cols(pm)

    pm = pm.rename(columns={
        "CUSTOMER MERGE": "customer",
        "ACCOUNTABILITY 4": "acc4",
        "ACCOUNTABILITY 5": "acc5",
        "UNITS": "units",
        "TN": "tn",
        "AGM": "agm",
        "SGM": "sgm"
    })[
        [
            "customer",
            "acc4",
            "acc5",
            "units",
            "tn",
            "agm",
            "sgm"
        ]
    ]
    pm = fix_customer(pm)

    pm["tn"] = pd.to_numeric(pm["tn"], errors="coerce")
    pm["agm"] = pd.to_numeric(pm["agm"], errors="coerce")
    pm["sgm"] = pd.to_numeric(pm["sgm"], errors="coerce")
    pm["units"] = pd.to_numeric(pm["units"], errors="coerce")

    pm = pm.fillna(0)

    pm = pm.groupby("customer", as_index=False)[["units", "tn", "agm", "sgm"]].sum()

    pm["SCENARIO"] = "PM"


    # ✅ CONCAT (ARTIK SAFE)
    df = pd.concat([act, bdg, ly, fcs, pm], ignore_index=True)

    return df, customer_attributes

def euro(x):
    if pd.isna(x):
        return ""
    if abs(x) >= 1_000_000:
        return f"€{x/1_000_000:.1f}M"
    elif abs(x) >= 1_000:
        return f"€{x/1_000:.1f}K"
    return f"€{x:.0f}"

def pct(x):
    if pd.isna(x):
        return ""
    return f"{x:.1f}%"

def pp(x):
    if pd.isna(x):
        return ""
    return f"{x:.1f} pp"
def number(x):
    if pd.isna(x):
        return ""
    return f"{x:,.2f}"   # 2 digit ✅

# ======================
# PAGE ✅
# ======================
def render_customer_overview():

    df, customer_attributes = load_data()

    # ======================
    # HEADER
    # ======================
    col_title, col_controls = st.columns([4, 2])

    with col_title:
        st.title("📊 Customer Performance-CHOOSE MONTH ON THE RIGHT--->")

    with col_controls:

        st.markdown("### ⚙️ Controls")

        # ✅ KPI DETAILS
        selected_scenarios = st.multiselect(
            "📊 Select Scenarios",
            ["ACT", "BDG", "FCS1", "LY", "PM"],
            default=[]
        )

        month_map = {
            "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4,
            "May": 5, "Jun": 6, "Jul": 7, "Aug": 8,
            "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
        }

        selected_month = st.selectbox(
            "Select last available month",
            list(month_map.keys()),
            index=5# ✅ change every month
        )

        months = month_map[selected_month]

        
       


    




    # ======================
    # PIVOT
    # ======================
    pivot = pd.pivot_table(
        df,
        index="customer",
        columns="SCENARIO",
        values=["units", "tn", "agm", "sgm"],
        aggfunc="sum",
        fill_value=0
    )

    pivot.columns = [f"{m}_{s}" for m, s in pivot.columns]
    pivot = pivot.reset_index()
    pivot = pivot.merge(
        customer_attributes,
        on="customer",
        how="left"
    )
    # ======================
    # FILTERS
    # ======================

    st.markdown("### 🔎 Filters")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        selected_acc4 = st.multiselect(
            "Accountability 4",
            sorted(
                customer_attributes["acc4"]
                .dropna()
                .astype(str)
                .unique()
            )
        )

    with col2:
        selected_acc5 = st.multiselect(
            "Accountability 5",
            sorted(
                customer_attributes["acc5"]
                .dropna()
                .astype(str)
                .unique()
            )
        )

    with col3:
        selected_application = st.multiselect(
            "Application",
            ["AG", "CE", "PG", "OTHER"]
        )

    with col4:
        selected_customers = st.multiselect(
            "Customer",
            sorted(pivot["customer"].unique())
        )

    # ======================
    # APPLY FILTERS ✅
    # ======================

    



    # ======================
    # CALC ✅
    # ======================
   
    pivot["tn_runrate"] = pivot["tn_ACT"] / months * 12
    
    pivot["margin_YTD"] = pivot["agm_ACT"] / pivot["tn_ACT"].replace(0, np.nan)
    
    pivot["agm_runrate"] = pivot["agm_ACT"] / months * 12

    pivot["margin_BDG"] = pivot["agm_BDG"] / pivot["tn_BDG"].replace(0, np.nan)
    pivot["margin_LY"] = pivot["agm_LY"] / pivot["tn_LY"].replace(0, np.nan)
    pivot["margin_FCS1"] = pivot["agm_FCS1"] / pivot["tn_FCS1"].replace(0, np.nan)
    pivot["margin_PM"] = pivot["agm_PM"] / pivot["tn_PM"].replace(0, np.nan)

    pivot["SGM%_BDG"] = pivot["sgm_BDG"] / pivot["tn_BDG"].replace(0, np.nan)
    pivot["SGM%_LY"] = pivot["sgm_LY"] / pivot["tn_LY"].replace(0, np.nan)
    pivot["SGM%_FCS1"] = pivot["sgm_FCS1"] / pivot["tn_FCS1"].replace(0, np.nan)
    pivot["SGM%_PM"] = pivot["sgm_PM"] / pivot["tn_PM"].replace(0, np.nan)
    pivot["SGM%_YTD"] = (pivot["sgm_ACT"]/ pivot["tn_ACT"].replace(0, np.nan))



    pivot["Δ_BDG_TN"] = (pivot["tn_runrate"] / pivot["tn_BDG"] - 1) * 100
    pivot["Δ_LY_TN"] = (pivot["tn_runrate"] / pivot["tn_LY"] - 1) * 100
    pivot["Δ_PM_TN"] = (pivot["tn_ACT"] / pivot["tn_PM"] - 1) * 100


    pivot["Δ_BDG_margin"] = (pivot["margin_YTD"] - pivot["margin_BDG"]) * 100
    pivot["Δ_LY_margin"] = (pivot["margin_YTD"] - pivot["margin_LY"]) * 100
    pivot["Δ_PM_margin"] = (pivot["margin_YTD"] - pivot["margin_PM"]) * 100

    pivot["Δ_BDG_SGM%"] = (pivot["SGM%_YTD"] - pivot["SGM%_BDG"]) * 100
    pivot["Δ_LY_SGM%"] = (pivot["SGM%_YTD"] - pivot["SGM%_LY"]) * 100
    pivot["Δ_PM_SGM%"] = (pivot["SGM%_YTD"] - pivot["SGM%_PM"]) * 100

    pivot["Δ_FCS1_TN"] = (pivot["tn_runrate"] / pivot["tn_FCS1"] - 1) * 100
    pivot["Δ_FCS1_margin"] = (pivot["margin_YTD"] - pivot["margin_FCS1"]) * 100
    pivot["Δ_FCS1_SGM%"] = (pivot["SGM%_YTD"]- pivot["SGM%_FCS1"]) * 100


    # ======================
    # APPLICATION MAPPING
    # ======================

    application_map = {
        "ARGO TRACTORS": "AG",
        "CARRARO ANTONIO": "AG",
        "CARRARO": "AG",
        "CLAAS": "AG",
        "DIECI": "AG",
        "HATTAT TRAKTOR SAN. TIC. A.S.": "AG",
        "HORSCH": "AG",
        "JCB LANDPOWER": "AG",
        "MERLO": "AG",

        "KOMATSU": "CE",
        "TIGERCAT": "CE",
        "LIEBHERR": "CE",

        "COELMO": "PG",
        "GENERAC": "PG",
        "HIMOINSA": "PG",
        "PRAMAC": "PG",
        "YANMAR": "PG",

        "ATLAS COPCO": "AG"
    }

    pivot["Application"] = (
        pivot["customer"]
        .map(application_map)
        .fillna("OTHER")
    )
    if selected_acc4:
        pivot = pivot[pivot["acc4"].isin(selected_acc4)]

    if selected_acc5:
        pivot = pivot[pivot["acc5"].isin(selected_acc5)]

    if selected_application:
        pivot = pivot[pivot["Application"].isin(selected_application)]

    if selected_customers:
        pivot = pivot[pivot["customer"].isin(selected_customers)]

    pivot = pivot[pivot["tn_ACT"] > 0]
    # ✅ EN BÜYÜK CUSTOMER ÜSTTE
    pivot = pivot.sort_values("tn_ACT", ascending=True)
    threshold = 1_000_000

    pivot.loc[pivot["tn_BDG"] < threshold, "Δ_BDG_TN"] = np.nan
    pivot.loc[pivot["tn_LY"] < threshold, "Δ_LY_TN"] = np.nan
    pivot.loc[pivot["tn_FCS1"] < threshold, "Δ_FCS1_TN"] = np.nan
    pivot.loc[pivot["tn_PM"] < threshold, "Δ_PM_TN"] = np.nan

    # ======================
    # KPI ✅
    # ======================
    st.markdown("## Overview")
    st.caption(f"""
    RunRate is calculated based on performance up to **{selected_month}**
    ({months} months YTD), annualized to full year.
    """)

    c1, c2, c3, c4, c5 = st.columns(5)

    total_tn = pivot["tn_runrate"].sum()
    total_agm = pivot["agm_runrate"].sum()
    total_sgm = pivot["sgm_ACT"].sum()
    total_margin = total_agm / total_tn if total_tn != 0 else np.nan
    total_tn_actual = pivot["tn_ACT"].sum()
    total_units = pivot["units_ACT"].sum()

    sgm_pct = (
        total_sgm / total_tn_actual
        if total_tn_actual != 0
        else np.nan
    )


    c1.metric("TN RunRate", euro(total_tn))
    c2.metric("AGM RunRate", euro(total_agm))
    c3.metric("Margin", pct(total_margin * 100))
    c4.metric("SGM %", pct(sgm_pct * 100))
    c5.metric("Units", f"{total_units:,}")

    st.markdown("## 🎯 Progress vs Budget")

    unit_completion = (
        pivot["units_ACT"].sum()
        /
        pivot["units_BDG"].sum()
    ) * 100 
    tn_completion = (
        pivot["tn_ACT"].sum()
        /
        pivot["tn_BDG"].sum()
    ) * 100

    agm_completion = (
        pivot["agm_ACT"].sum()
        /
        pivot["agm_BDG"].sum()
    ) * 100

    sgm_completion = (
        pivot["sgm_ACT"].sum()
        /
        pivot["sgm_BDG"].sum()
    ) * 100

    actual_margin = (
        pivot["agm_ACT"].sum()
        /
        pivot["tn_ACT"].sum()
    ) * 100

    budget_margin = (
        pivot["agm_BDG"].sum()
        /
        pivot["tn_BDG"].sum()
    ) * 100

    margin_completion = (
        actual_margin /
        budget_margin
    ) * 100

    def create_donut(value, title):

        if pd.isna(value) or np.isinf(value):
            value = 0

        value = float(value)
        value = max(0, min(value, 100))

        fig = go.Figure(
            data=[
                go.Pie(
                    values=[value, 100-value],
                    hole=0.7,
                    marker_colors=["#DE2ECF", "#EAEDED"],
                    textinfo="none"
                )
            ]
        )

        fig.update_layout(
            title=f"{title}<br><b>{value:.0f}%</b>",
            height=250,
            margin=dict(t=40, b=20, l=20, r=20),
            showlegend=False
        )

        return fig

    d1, d2, d3, d4, d5 = st.columns(5)

    with d1:
        st.plotly_chart(
            create_donut(tn_completion, "TN"),
            use_container_width=True,
            key="budget_tn"
        )

        st.caption(
            f"Actual: {euro(pivot['tn_ACT'].sum())} / "
            f"BDG: {euro(pivot['tn_BDG'].sum())}"
        )

    with d2:
        st.plotly_chart(
            create_donut(agm_completion, "AGM"),
            use_container_width=True,
            key="budget_agm"
        )

        st.caption(
            f"Actual: {euro(pivot['agm_ACT'].sum())} / "
            f"BDG: {euro(pivot['agm_BDG'].sum())}"
        )

    with d3:
        st.plotly_chart(
            create_donut(sgm_completion, "SGM"),
            use_container_width=True,
            key="budget_sgm"
        )
        

        st.caption(
            f"Actual: {euro(pivot['sgm_ACT'].sum())} / "
            f"BDG: {euro(pivot['sgm_BDG'].sum())}"
        )

    with d4:
        st.plotly_chart(
            create_donut(margin_completion, "Margin"),
            use_container_width=True,
            key="budget_margin"
        )
        

        st.caption(
            f"Actual: {actual_margin:.1f}%"
            f" | BDG: {budget_margin:.1f}%"
        )

    with d5:
        st.plotly_chart(
            create_donut(unit_completion, "Units"),
            use_container_width=True,
            key="budget_units"
        )
        

        st.caption(
            f"Actual: {pivot['units_ACT'].sum():,} / "
            f"BDG: {pivot['units_BDG'].sum():,}"
        )



    st.markdown("## 🔮 Progress vs Forecast")
    unit_fcs = (
        pivot["units_ACT"].sum()
        /
        pivot["units_FCS1"].sum()
    ) * 100
    tn_fcs = (
        pivot["tn_ACT"].sum()
        /
        pivot["tn_FCS1"].sum()
    ) * 100

    agm_fcs = (
        pivot["agm_ACT"].sum()
        /
        pivot["agm_FCS1"].sum()
    ) * 100

    sgm_fcs = (
        pivot["sgm_ACT"].sum()
        /
        pivot["sgm_FCS1"].sum()
    ) * 100

    forecast_margin = (
        pivot["agm_FCS1"].sum()
        /
        pivot["tn_FCS1"].sum()
    ) * 100

    margin_fcs = (
        actual_margin
        /
        forecast_margin
    ) * 100

    f1, f2, f3, f4, f5 = st.columns(5)

    with f1:
        st.plotly_chart(
            create_donut(tn_fcs, "TN"),
            use_container_width=True,
            key="forecast_tn"
        )

        st.caption(
            f"Actual: {euro(pivot['tn_ACT'].sum())}"
            f" | FCS: {euro(pivot['tn_FCS1'].sum())}"
        )

    with f2:
        st.plotly_chart(
            create_donut(agm_fcs, "AGM"),
            use_container_width=True,
            key="forecast_agm"
        )

        st.caption(
            f"Actual: {euro(pivot['agm_ACT'].sum())}"
            f" | FCS: {euro(pivot['agm_FCS1'].sum())}"
        )

    with f3:
        st.plotly_chart(
            create_donut(sgm_fcs, "SGM"),
            use_container_width=True,
            key="forecast_sgm"
        )

        st.caption(
            f"Actual: {euro(pivot['sgm_ACT'].sum())}"
            f" | FCS: {euro(pivot['sgm_FCS1'].sum())}"
        )

    with f4:
        st.plotly_chart(
            create_donut(margin_fcs, "Margin"),
            use_container_width=True,
            key="forecast_margin"
        )

        st.caption(
            f"Actual: {actual_margin:.1f}%"
            f" | FCS: {forecast_margin:.1f}%"
        )

    with f5:
        st.plotly_chart(
            create_donut(unit_fcs, "Units"),
            use_container_width=True,
            key="forecast_units"
        )

        st.caption(
            f"Actual: {euro(pivot['units_ACT'].sum())}"
            f" | FCS: {euro(pivot['units_FCS1'].sum())}"
        )

    st.markdown("## 📅 Customer Improvement vs Previous Month")

    pm_table = pivot.copy()

    pm_table["Margin PM"] = pm_table["margin_PM"] * 100
    pm_table["Margin Now"] = pm_table["margin_YTD"] * 100

    pm_table["TN Now"] = pm_table["tn_ACT"]
    pm_table["TN PM"] = pm_table["tn_PM"]

    pm_table["Δ Margin"] = pm_table["Δ_PM_margin"]
    pm_table["Δ TN"] = pm_table["Δ_PM_TN"]

    best_pm = pm_table.sort_values(
        "Δ Margin",
        ascending=False
    ).head(5)

    worst_pm = pm_table.sort_values(
        "Δ Margin",
        ascending=True
    ).head(5)

    col1, col2 = st.columns(2)

    # ==========================
    # TOP IMPROVED
    # ==========================
    with col1:

        st.markdown("### 🟢 Top 5 Improved vs PM")

        display_best = best_pm[
            [
                "customer",
                "Application",
                "Margin PM",
                "Margin Now",
                "Δ Margin",
                "TN PM",
                "TN Now",
                "Δ TN"
            ]
        ].copy()

        # format first
        display_best["Margin PM"] = display_best["Margin PM"].round(1)
        display_best["Margin Now"] = display_best["Margin Now"].round(1)
        display_best["Δ Margin"] = display_best["Δ Margin"].round(1)
        display_best["Δ TN"] = display_best["Δ TN"].round(1)

        display_best["TN PM"] = display_best["TN PM"].apply(euro)
        display_best["TN Now"] = display_best["TN Now"].apply(euro)

        # rename last
        display_best = display_best.rename(columns={
            "customer": "Customer",
            "Application": "App",
            "Margin PM": "PM Margin %",
            "Margin Now": "Current Margin %",
            "Δ Margin": "Δ Margin (pp)",
            "TN PM": "PM TN",
            "TN Now": "Current TN",
            "Δ TN": "Δ TN (%)"
        })

        st.dataframe(
            display_best,
            use_container_width=True
        )

    # ==========================
    # TOP DETERIORATED
    # ==========================
    with col2:

        st.markdown("### 🔴 Top 5 Deteriorated vs PM")

        display_worst = worst_pm[
            [
                "customer",
                "Application",
                "Margin PM",
                "Margin Now",
                "Δ Margin",
                "TN PM",
                "TN Now",
                "Δ TN"
            ]
        ].copy()

        # format first
        display_worst["Margin PM"] = display_worst["Margin PM"].round(1)
        display_worst["Margin Now"] = display_worst["Margin Now"].round(1)
        display_worst["Δ Margin"] = display_worst["Δ Margin"].round(1)
        display_worst["Δ TN"] = display_worst["Δ TN"].round(1)

        display_worst["TN PM"] = display_worst["TN PM"].apply(euro)
        display_worst["TN Now"] = display_worst["TN Now"].apply(euro)

        # rename last
        display_worst = display_worst.rename(columns={
            "customer": "Customer",
            "Application": "App",
            "Margin PM": "PM Margin %",
            "Margin Now": "Current Margin %",
            "Δ Margin": "Δ Margin (pp)",
            "TN PM": "PM TN",
            "TN Now": "Current TN",
            "Δ TN": "Δ TN (%)"
        })

        st.dataframe(
            display_worst,
            use_container_width=True
        )

    st.markdown("## 🥧 Application Mix Analysis")

    c1, c2, c3, c4 = st.columns(4)

    # =====================
    # TN MIX
    # =====================

    tn_mix = (
        pivot.groupby("Application")["tn_ACT"]
        .sum()
        .reset_index()
    )

    fig_tn = px.pie(
        tn_mix,
        names="Application",
        values="tn_ACT",
        hole=0.45,
        title=f"TN ({selected_month} YTD)"
    )

    fig_tn.update_traces(
        textposition="inside",
        texttemplate="%{label}<br>%{percent}<br>€%{value:,.0f}"
    )

    with c1:
        st.plotly_chart(
            fig_tn,
            use_container_width=True
        )
    
    # =====================
    # AGM MIX
    # =====================

    agm_mix = (
        pivot.groupby("Application")["agm_ACT"]
        .sum()
        .reset_index()
    )

    fig_agm = px.pie(
        agm_mix,
        names="Application",
        values="agm_ACT",
        hole=0.45,
        title=f"AGM ({selected_month} YTD)"
    )

    fig_agm.update_traces(
        textposition="inside",
        texttemplate="%{label}<br>%{percent}<br>€%{value:,.0f}"
    )

    with c2:
        st.plotly_chart(
            fig_agm,
            use_container_width=True
        )

    # =====================
    # SGM MIX
    # =====================

    sgm_mix = (
        pivot.groupby("Application")["sgm_ACT"]
        .sum()
        .reset_index()
    )

    fig_sgm = px.pie(
        sgm_mix,
        names="Application",
        values="sgm_ACT",
        hole=0.45,
        title=f"SGM ({selected_month} YTD)"
    )

    fig_sgm.update_traces(
        textposition="inside",
        texttemplate="%{label}<br>%{percent}<br>€%{value:,.0f}"
    )

    with c3:
        st.plotly_chart(
            fig_sgm,
            use_container_width=True
        )

    # =====================
    # CUSTOMER MIX
    # =====================

    unit_mix = (
        pivot.groupby("Application")["units_ACT"]
        .sum()
        .reset_index()
    )

    fig_unit = px.pie(
        unit_mix,
        names="Application",
        values="units_ACT",
        hole=0.45,
        title=f"Units ({selected_month} YTD)"
    )

    fig_unit.update_traces(
        textposition="inside",
        texttemplate="%{label}<br>%{percent}<br>%{value:,.0f}"
    )

    with c4:
        st.plotly_chart(
            fig_unit,
            use_container_width=True
        )
    mix_summary = (
        pivot.groupby("Application")
        .agg({
            "tn_ACT": "sum",
            "agm_ACT": "sum",
            "sgm_ACT": "sum",
            "units_ACT": "sum"
        })
        .reset_index()
    )
    mix_summary["ACT Units"] = (
        mix_summary["units_ACT"]
        .map(lambda x: f"{x:,.0f}")
    )
    mix_summary["ACT AGM %"] = (
        mix_summary["agm_ACT"]
        /
        mix_summary["tn_ACT"].replace(0, np.nan)
    ) * 100

    mix_summary["ACT SGM %"] = (
        mix_summary["sgm_ACT"]
        /
        mix_summary["tn_ACT"].replace(0, np.nan)
    ) * 100

    mix_summary["ACT TN"] = mix_summary["tn_ACT"].apply(euro)
    mix_summary["ACT AGM"] = mix_summary["agm_ACT"].apply(euro)
    mix_summary["ACT SGM"] = mix_summary["sgm_ACT"].apply(euro)

    mix_summary["ACT AGM %"] = mix_summary["ACT AGM %"].apply(
        lambda x: f"{x:.1f}%"
    )

    mix_summary["ACT SGM %"] = mix_summary["ACT SGM %"].apply(
        lambda x: f"{x:.1f}%"
)

    st.dataframe(
        mix_summary[
            [
                "Application",
                "ACT TN",
                "ACT AGM",
                "ACT AGM %",
                "ACT SGM",
                "ACT SGM %",
                "ACT Units"
            ]
        ],
        hide_index=True,
        use_container_width=True
    )
    st.markdown("## 🎯 Application Performance vs Targets")

    app_summary = (
        pivot.groupby("Application")
        .agg({
            "tn_ACT": "sum",
            "agm_ACT": "sum",
            "sgm_ACT": "sum",
            "tn_BDG": "sum",
            "agm_BDG": "sum",
            "sgm_BDG": "sum",
            "tn_FCS1": "sum",
            "agm_FCS1": "sum",
            "sgm_FCS1": "sum",
            "tn_PM": "sum",
            "agm_PM": "sum",
            "sgm_PM": "sum"
        })
        .reset_index()
    )

    # =====================
    # MARGIN %
    # =====================

    app_summary["Margin_ACT"] = (
        app_summary["agm_ACT"]
        / app_summary["tn_ACT"].replace(0, np.nan)
    )

    app_summary["Margin_BDG"] = (
        app_summary["agm_BDG"]
        / app_summary["tn_BDG"].replace(0, np.nan)
    )

    app_summary["Margin_FCS"] = (
        app_summary["agm_FCS1"]
        / app_summary["tn_FCS1"].replace(0, np.nan)
    )

    app_summary["Margin_PM"] = (
        app_summary["agm_PM"]
        / app_summary["tn_PM"].replace(0, np.nan)
    )

    # =====================
    # SGM %
    # =====================

    app_summary["SGM_ACT"] = (
        app_summary["sgm_ACT"]
        / app_summary["tn_ACT"].replace(0, np.nan)
    )

    app_summary["SGM_BDG"] = (
        app_summary["sgm_BDG"]
        / app_summary["tn_BDG"].replace(0, np.nan)
    )

    app_summary["SGM_FCS"] = (
        app_summary["sgm_FCS1"]
        / app_summary["tn_FCS1"].replace(0, np.nan)
    )

    app_summary["SGM_PM"] = (
        app_summary["sgm_PM"]
        / app_summary["tn_PM"].replace(0, np.nan)
    )

    # =====================
    # DELTAS (PP)
    # =====================

    app_summary["Margin vs BDG"] = (
        app_summary["Margin_ACT"]
        - app_summary["Margin_BDG"]
    ) * 100

    app_summary["Margin vs FCS"] = (
        app_summary["Margin_ACT"]
        - app_summary["Margin_FCS"]
    ) * 100

    app_summary["Margin vs PM"] = (
        app_summary["Margin_ACT"]
        - app_summary["Margin_PM"]
    ) * 100

    app_summary["SGM vs BDG"] = (
        app_summary["SGM_ACT"]
        - app_summary["SGM_BDG"]
    ) * 100

    app_summary["SGM vs FCS"] = (
        app_summary["SGM_ACT"]
        - app_summary["SGM_FCS"]
    ) * 100

    app_summary["SGM vs PM"] = (
        app_summary["SGM_ACT"]
        - app_summary["SGM_PM"]
    ) * 100

    # =====================
    # FORMAT
    # =====================

    for col in [
        "Margin vs BDG",
        "Margin vs FCS",
        "Margin vs PM",
        "SGM vs BDG",
        "SGM vs FCS",
        "SGM vs PM"
    ]:
        app_summary[col] = app_summary[col].apply(
            lambda x: f"{x:+.1f} pp" if pd.notna(x) else ""
        )

    # =====================
    # DISPLAY
    # =====================

    st.dataframe(
        app_summary[
            [
                "Application",
                "Margin vs BDG",
                "Margin vs FCS",
                "Margin vs PM",
                "SGM vs BDG",
                "SGM vs FCS",
                "SGM vs PM"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

    # ======================
    # TABLE ✅ (AYNI FORMAT)
    # ======================
    rows = []


    for _, r in pivot.iterrows():

        # AGM
        rows.append({
            "Customer": r["customer"],
            "Type": "AGM",
            "Metric": f"AGM RunRate ({selected_month} YTD): {euro(r['agm_runrate'])}",
            "ACT (€)": euro(r["agm_runrate"]),
            "Margin (%)": pct(r["margin_YTD"] * 100),
            "Δ BDG": pp(r["Δ_BDG_margin"]),
            "Δ FCS1": pp(r["Δ_FCS1_margin"]),
            "Δ LY": pp(r["Δ_LY_margin"]),
            "Δ PM": pp(r["Δ_PM_margin"])
        })

        # SGM
        rows.append({
            "Customer": r["customer"],
            "Type": "SGM",
            "Metric": f"SGM Actual ({selected_month} YTD): {euro(r['sgm_ACT'])}",

            "ACT (€)": euro(r["sgm_ACT"]),
            "Margin (%)": pct(r["SGM%_YTD"] * 100),
            "Δ BDG": pp(r["Δ_BDG_SGM%"]),
            "Δ FCS1": pp(r["Δ_FCS1_SGM%"]),
            "Δ LY": pp(r["Δ_LY_SGM%"]),
            "Δ PM": pp(r["Δ_PM_SGM%"]),
        })

        # TN
        rows.append({
            "Customer": r["customer"],
            "Type": "TN",
            "Metric": f"TN RunRate ({selected_month} YTD): {euro(r['tn_runrate'])}",
            "ACT (€)": euro(r["tn_runrate"]),
            "Margin (%)": "",
            "Δ BDG": pp(r["Δ_BDG_TN"]),
            "Δ FCS1": pp(r["Δ_FCS1_TN"]),
            "Δ LY": pp(r["Δ_LY_TN"]),
            "Δ PM": pp(r["Δ_PM_TN"]),
        })


    final_df = pd.DataFrame(rows)

    def highlight(val):
        try:
            txt = str(val).replace("%","").replace("pp","").strip()
            v = float(txt)
        except:
            return ""

        if v > 1:
            return "background-color: #c6f7d0"
        elif v < -1:
            return "background-color: #f7c6c7"
        else:
            return "background-color: #fff3cd"



    styled = final_df.style.map(highlight, subset=["Δ BDG","Δ FCS1","Δ LY","Δ PM"])
    st.markdown("""
    🟢 **Metric Definitions**

    - € Values → **RunRate (Annualized)**
    - % Values → **Actual (YTD)**
    - Δ (pp) → **Actual Margin Difference**
    - Δ (%) → **RunRate vs Target**
    """)
    st.dataframe(styled, use_container_width=True, height=650)

        # ======================
    # KPI DETAILS ✅
    # ======================

    if selected_scenarios:
        st.markdown("## 📊 KPI Details")

    if "ACT" in selected_scenarios:
        with st.expander("📘 ACT Details"):

            df_act = pivot[[
                "customer",
                "tn_ACT",
                "agm_ACT",
                "sgm_ACT",
                "margin_YTD",
                "tn_runrate",
                "agm_runrate"
                
            ]].copy()

            # ===== FORMAT =====
            df_act["TN"] = df_act["tn_ACT"].apply(number)
            df_act["AGM (€)"] = df_act["agm_ACT"].apply(euro)
            df_act["Margin (%)"] = df_act["margin_YTD"].apply(lambda x: f"{x*100:.2f}%")
            df_act["SGM (€)"] = df_act["sgm_ACT"].apply(euro)

            df_act["RunRate TN"] = df_act["tn_runrate"].apply(euro)
            df_act["RunRate AGM"] = df_act["agm_runrate"].apply(euro)
            

            st.dataframe(
                df_act[[
                    "customer",
                    "TN",
                    "AGM (€)",
                    "SGM (€)",
                    "Margin (%)",
                    "RunRate TN",
                    "RunRate AGM"
                ]],
                use_container_width=True
            )


    if "BDG" in selected_scenarios:
        with st.expander("💰 Budget (BDG)"):

            df_bdg = pivot[[
                "customer",
                "tn_ACT","tn_BDG",
                "agm_ACT","agm_BDG",
                "sgm_ACT","sgm_BDG",
                "margin_YTD","margin_BDG"
            ]].copy()

            df_bdg["TN ACT"] = df_bdg["tn_ACT"].apply(number)
            df_bdg["TN BDG"] = df_bdg["tn_BDG"].apply(number)

            df_bdg["AGM ACT (€)"] = df_bdg["agm_ACT"].apply(euro)
            df_bdg["AGM BDG (€)"] = df_bdg["agm_BDG"].apply(euro)
            df_bdg["SGM ACT (€)"] = df_bdg["sgm_ACT"].apply(euro)
            df_bdg["SGM BDG (€)"] = df_bdg["sgm_BDG"].apply(euro)

            df_bdg["Margin ACT (%)"] = df_bdg["margin_YTD"].apply(lambda x: f"{x*100:.2f}%")
            df_bdg["Margin BDG (%)"] = df_bdg["margin_BDG"].apply(lambda x: f"{x*100:.2f}%")

            st.dataframe(
                df_bdg[[
                    "customer",
                    "TN ACT","TN BDG",
                    "AGM ACT (€)","AGM BDG (€)",
                    "SGM ACT (€)","SGM BDG (€)",
                    "Margin ACT (%)","Margin BDG (%)"
                ]],
                use_container_width=True
            )

    if "FCS1" in selected_scenarios:
        with st.expander("🔮 Forecast (FCS1)"):

            df_fcs = pivot[[
                "customer",
                "tn_ACT","tn_FCS1",
                "agm_ACT","agm_FCS1",
                "sgm_ACT","sgm_FCS1",
                "margin_YTD","margin_FCS1"
            ]].copy()

            df_fcs["TN ACT"] = df_fcs["tn_ACT"].apply(number)
            df_fcs["TN FCS"] = df_fcs["tn_FCS1"].apply(number)

            df_fcs["AGM ACT (€)"] = df_fcs["agm_ACT"].apply(euro)
            df_fcs["AGM FCS (€)"] = df_fcs["agm_FCS1"].apply(euro)
            df_fcs["SGM ACT (€)"] = df_fcs["sgm_ACT"].apply(euro)
            df_fcs["SGM FCS (€)"] = df_fcs["sgm_FCS1"].apply(euro)

            df_fcs["Margin ACT (%)"] = df_fcs["margin_YTD"].apply(lambda x: f"{x*100:.2f}%")
            df_fcs["Margin FCS (%)"] = df_fcs["margin_FCS1"].apply(lambda x: f"{x*100:.2f}%")

            st.dataframe(
                df_fcs[[
                    "customer",
                    "TN ACT","TN FCS",
                    "AGM ACT (€)","AGM FCS (€)",
                    "SGM ACT (€)","SGM FCS (€)",
                    "Margin ACT (%)","Margin FCS (%)"
                ]],
                use_container_width=True
            )

    if "LY" in selected_scenarios:
        with st.expander("📉 Last Year (LY)"):

            df_ly = pivot[[
                "customer",
                "tn_ACT","tn_LY",
                "agm_ACT","agm_LY",
                "sgm_ACT","sgm_LY",
                "margin_YTD","margin_LY"
            ]].copy()

            df_ly["TN ACT"] = df_ly["tn_ACT"].apply(number)
            df_ly["TN LY"] = df_ly["tn_LY"].apply(number)

            df_ly["AGM ACT (€)"] = df_ly["agm_ACT"].apply(euro)
            df_ly["AGM LY (€)"] = df_ly["agm_LY"].apply(euro)

            df_ly["SGM ACT (€)"] = df_ly["sgm_ACT"].apply(euro)
            df_ly["SGM LY (€)"] = df_ly["sgm_LY"].apply(euro)

            df_ly["Margin ACT (%)"] = df_ly["margin_YTD"].apply(lambda x: f"{x*100:.2f}%")
            df_ly["Margin LY (%)"] = df_ly["margin_LY"].apply(lambda x: f"{x*100:.2f}%")

            st.dataframe(
                df_ly[[
                    "customer",
                    "TN ACT","TN LY",
                    "AGM ACT (€)","AGM LY (€)",
                    "SGM ACT (€)","SGM LY (€)",
                    "Margin ACT (%)","Margin LY (%)"
                ]],
                use_container_width=True
            )
    if "PM" in selected_scenarios:
        with st.expander("📅 Previous Month (PM)"):

            df_pm = pivot[[
                "customer",
                "tn_ACT","tn_PM",
                "agm_ACT","agm_PM",
                "sgm_ACT","sgm_PM",
                "margin_YTD","margin_PM"
            ]].copy()

            df_pm["TN ACT"] = df_pm["tn_ACT"].apply(number)
            df_pm["TN PM"] = df_pm["tn_PM"].apply(number)

            df_pm["AGM ACT (€)"] = df_pm["agm_ACT"].apply(euro)
            df_pm["AGM PM (€)"] = df_pm["agm_PM"].apply(euro)

            df_pm["SGM ACT (€)"] = df_pm["sgm_ACT"].apply(euro)
            df_pm["SGM PM (€)"] = df_pm["sgm_PM"].apply(euro)

            df_pm["Margin ACT (%)"] = df_pm["margin_YTD"].apply(
                lambda x: f"{x*100:.2f}%"
            )

            df_pm["Margin PM (%)"] = df_pm["margin_PM"].apply(
                lambda x: f"{x*100:.2f}%"
            )

            st.dataframe(
                df_pm[[
                    "customer",
                    "TN ACT",
                    "TN PM",
                    "AGM ACT (€)",
                    "AGM PM (€)",
                    "SGM ACT (€)",
                    "SGM PM (€)",
                    "Margin ACT (%)",
                    "Margin PM (%)"
                ]],
                use_container_width=True
            )

    # ✅ TEMİZ HEADERS
    def clean_col(c):
        c = c.replace("_", " ")
        c = c.replace("Tn", "TN")
        c = c.replace("Agm", "AGM")
        c = c.replace("Sgm", "SGM")
        return c

    final_df.columns = [clean_col(c) for c in final_df.columns]
    # ✅ EURO FORMAT
    for c in [
        "tn ACT","tn BDG","tn FCS1","tn LY",
        "agm ACT","agm BDG","agm FCS1","agm LY",
        "sgm ACT","sgm BDG","sgm FCS1","sgm LY"
    ]:
        if c in final_df.columns:
            final_df[c] = final_df[c].apply(euro)

    # ✅ MARGIN FORMAT
    for c in [
        "margin YTD","margin BDG","margin FCS1","margin LY"
    ]:
        if c in final_df.columns:
            final_df[c] = final_df[c].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "")

    # ✅ TN SATIRINDA AGM GİZLE
    def clean_row(row):
        if row["Type"] == "TN":
            for c in ["AGM ACT","AGM BDG","AGM FCS1","AGM LY"]:
                if c in row:
                    row[c] = ""

            for c in ["SGM ACT","SGM BDG","SGM FCS1","SGM LY"]:
                if c in row:
                    row[c] = ""

            for c in ["MARGIN YTD","MARGIN BDG","MARGIN FCS1","MARGIN LY"]:
                if c in row:
                    row[c] = ""

        return row

    final_df = final_df.apply(clean_row, axis=1)
    # ✅ ÖNEMLİ KOLONLAR İLK GÖRÜNSÜN
    main_cols = [
        "Customer",
        "Type",
        "Metric",
        "ACT (€)",
        "Margin (%)",
        "Δ BDG",
        "Δ FCS1",
        "Δ LY",
        "Δ PM"
    ]

    other_cols = [c for c in final_df.columns if c not in main_cols]

    final_df = final_df[main_cols + other_cols]



    st.markdown("---")
    st.markdown("## 📊 Insights")

    def prepare_display(df, ref):
        d = df.copy()

        d["TN ACT"] = d["tn_ACT"].apply(euro)
        d[f"TN {ref}"] = d[f"tn_{ref}"].apply(euro)
        d["SGM ACT"] = d["sgm_ACT"].apply(euro)
        d[f"SGM {ref}"] = d[f"sgm_{ref}"].apply(euro)

        d["AGM ACT"] = d["agm_ACT"].apply(euro)
        d[f"AGM {ref}"] = d[f"agm_{ref}"].apply(euro)

        d["Margin ACT"] = d["margin_YTD"].apply(lambda x: f"{x*100:.1f}%")
        d[f"Margin {ref}"] = d[f"margin_{ref}"].apply(lambda x: f"{x*100:.1f}%")

        d["Δ Margin Raw"] = d[f"Δ_{ref}_margin"]

        d["Δ Margin"] = d["Δ Margin Raw"].apply(lambda x: f"{x:+.1f} pp")

        d["Insight"] = d["Δ Margin Raw"].apply(
            lambda x:
            "✅ On target" if abs(x) < 1 else
            "🟢 Above target" if x > 0 else
            "🔴 Below target"
        )

        return d


    def style_delta(df):
        def color(val):
            try:
                v = float(str(val).replace("pp",""))
            except:
                return ""

            if v > 1:
                return "background-color: #c6f7d0; font-weight:bold;"
            elif v < -1:
                return "background-color: #f7c6c7; font-weight:bold;"
            else:
                return "background-color: #fff3cd;"

        return df.style.map(color, subset=["Δ Margin"])


    # ======================
    # BUDGET
    # ======================

    st.markdown("### 💰 Vs Budget")

    col1, col2 = st.columns(2)

    closest = pivot.loc[pivot["Δ_BDG_margin"].abs().sort_values().index].head(5)
    furthest = pivot.loc[pivot["Δ_BDG_margin"].abs().sort_values(ascending=False).index].head(5)

    with col1:
        st.markdown("✅ Best (Closest to Budget)")
        df1 = prepare_display(closest, "BDG")
        st.dataframe(
            style_delta(df1[[
                "customer","TN ACT","TN BDG",
                "AGM ACT","AGM BDG",
                "Margin ACT","Margin BDG",
                "SGM ACT","SGM BDG",
                "Δ Margin","Insight"
            ]]),
            use_container_width=True
        )

    with col2:
        st.markdown("🔴 Worst (Furthest from Budget)")
        df2 = prepare_display(furthest, "BDG")
        st.dataframe(
            style_delta(df2[[
                "customer","TN ACT","TN BDG",
                "AGM ACT","AGM BDG",
                "Margin ACT","Margin BDG",
                "SGM ACT","SGM BDG",
                "Δ Margin","Insight"
            ]]),
            use_container_width=True
        )


    # ======================
    # FCS
    # ======================

    st.markdown("### 🔮 Vs Forecast")

    col1, col2 = st.columns(2)

    closest_fc = pivot.loc[pivot["Δ_FCS1_margin"].abs().sort_values().index].head(5)
    furthest_fc = pivot.loc[pivot["Δ_FCS1_margin"].abs().sort_values(ascending=False).index].head(5)

    with col1:
        st.markdown("✅ Best (Closest to Forecast)")
        df3 = prepare_display(closest_fc, "FCS1")
        st.dataframe(
            style_delta(df3[[
                "customer","TN ACT","TN FCS1",
                "AGM ACT","AGM FCS1",
                "Margin ACT","Margin FCS1",
                "SGM ACT","SGM FCS1",
                "Δ Margin","Insight"
            ]]),
            use_container_width=True
        )

    with col2:
        st.markdown("🔴 Worst (Furthest from Forecast)")
        df4 = prepare_display(furthest_fc, "FCS1")
        st.dataframe(
            style_delta(df4[[
                "customer","TN ACT","TN FCS1",
                "AGM ACT","AGM FCS1",
                "Margin ACT","Margin FCS1",
                "SGM ACT","SGM FCS1",
                "Δ Margin","Insight"
            ]]),
            use_container_width=True
        )


    # ======================
    # LY
    # ======================

    st.markdown("### 📉 Vs Last Year")

    col1, col2 = st.columns(2)

    best = pivot.loc[pivot["Δ_LY_margin"].sort_values(ascending=False).index].head(5)
    worst = pivot.loc[pivot["Δ_LY_margin"].sort_values().index].head(5)

    def prepare_display_ly(df):
        d = df.copy()

        d["TN ACT"] = d["tn_ACT"].apply(euro)
        d["TN LY"] = d["tn_LY"].apply(euro)
        d["SGM ACT"] = d["sgm_ACT"].apply(euro)
        d["SGM LY"] = d["sgm_LY"].apply(euro)

        d["AGM ACT"] = d["agm_ACT"].apply(euro)
        d["AGM LY"] = d["agm_LY"].apply(euro)

        d["Margin ACT"] = d["margin_YTD"].apply(lambda x: f"{x*100:.1f}%")
        d["Margin LY"] = d["margin_LY"].apply(lambda x: f"{x*100:.1f}%")

        d["Δ Margin Raw"] = d["Δ_LY_margin"]
        d["Δ Margin"] = d["Δ Margin Raw"].apply(lambda x: f"{x:+.1f} pp")

        d["Insight"] = d["Δ Margin Raw"].apply(
            lambda x: "🟢 Improved" if x > 0 else "🔴 Deteriorated"
        )

        return d

    with col1:
        st.markdown("🟢 Best vs LY")
        df5 = prepare_display_ly(best)
        st.dataframe(
            style_delta(df5[[
                "customer","TN ACT","TN LY",
                "AGM ACT","AGM LY",
                "Margin ACT","Margin LY",
                "SGM ACT","SGM LY",
                "Δ Margin","Insight"
            ]]),
            use_container_width=True
        )

    with col2:
        st.markdown("🔴 Worst vs LY")
        df6 = prepare_display_ly(worst)
        st.dataframe(
            style_delta(df6[[
                "customer","TN ACT","TN LY",
                "AGM ACT","AGM LY",
                "Margin ACT","Margin LY",
                "SGM ACT","SGM LY",
                "Δ Margin","Insight"
            ]]),
            use_container_width=True
        )


    st.markdown("---")
    st.markdown(f"## 📈 RunRate Performance Analysis ({selected_month} YTD)")
    st.caption("""
    All € values are RunRate-based (annualized).
    Margins (%) are based on Actual YTD performance.
    """)
    
    
    st.info(f"""
    💡 **How to read this table**

    • Based on data up to **{selected_month}**  
    • {months} months YTD used  
    • € = RunRate (annualized)  
    • % = Actual performance  
    """)

    st.info(f"📅 Data loaded up to {selected_month}")



    # ✅ BURAYA KOY ↓↓↓
    def highlight_delta(val):
        try:
            v = float(str(val).replace("%","").replace("pp","").strip())
        except:
            return ""

        if v > 1:
            return "background-color: #c6f7d0"
        elif v < -1:
            return "background-color: #f7c6c7"
        else:
            return "background-color: #fff3cd"

    # ✅ SONRA DEVAM
    col1, col2 = st.columns(2)


    def build_analysis(df, ref):

        d = df.copy()

        # ===== CALC =====
        d["tn_runrate"] = d["tn_runrate"]
        d["tn_ref"] = d[f"tn_{ref}"]

        d["agm_runrate"] = d["agm_runrate"]
        d["agm_ref"] = d[f"agm_{ref}"]

        d["margin_runrate"] = d["margin_YTD"]
        d["margin_ref"] = d[f"margin_{ref}"]

        d["Δ_TN"] = (d["tn_runrate"] / d["tn_ref"] - 1) * 100
        d["Δ_margin"] = (d["margin_runrate"] - d["margin_ref"]) * 100

       

      


        # ===== FORMAT =====
        d["RunRate TN"] = d["tn_runrate"].apply(euro)
        d[f"{ref} TN"] = d["tn_ref"].apply(euro)

        d["RunRate AGM"] = d["agm_runrate"].apply(euro)
        d[f"{ref} AGM"] = d["agm_ref"].apply(euro)

  

        d["Margin RunRate"] = d["margin_runrate"].apply(lambda x: f"{x*100:.1f}%")
        d[f"Margin {ref}"] = d["margin_ref"].apply(lambda x: f"{x*100:.1f}%")

        d["Δ TN"] = d["Δ_TN"].apply(lambda x: f"{x:+.1f}%")
        d["Δ Margin"] = d["Δ_margin"].apply(lambda x: f"{x:+.1f} pp")
    
        # ===== INSIGHT =====
        def insight(row):
            tn = row["Δ_TN"]
            m = row["Δ_margin"]

            if pd.isna(tn) or pd.isna(m):
                return ""

            # BOTH GOOD
            if m > 0 and tn > 0:
                return "Margin ↑ & Volume ↑"

            # MIXED CASES
            elif m > 0 and tn < 0:
                return "Margin ↑ & Volume ↓"

            elif m < 0 and tn > 0:
                return "Margin ↓ & Volume ↑"

            # BOTH BAD
            elif m < 0 and tn < 0:
                return "Margin ↓ & Volume ↓"

            return ""

        d["Insight"] = d.apply(insight, axis=1)

        # ===== SORT =====
        d = d.sort_values("Δ_margin", ascending=True)

        return d[[
            "customer",
            "RunRate TN", f"{ref} TN",
            "RunRate AGM", f"{ref} AGM",
            "Margin RunRate", f"Margin {ref}",
         
            "Δ TN", "Δ Margin", 
            "Insight"
        ]]
    
    def build_analysis_actual(df, ref):

        d = df.copy()

        # ===== ACTUAL BASE =====
        d["tn_actual"] = d["tn_ACT"]
        d["tn_ref"] = d[f"tn_{ref}"]

        d["agm_actual"] = d["agm_ACT"]
        d["agm_ref"] = d[f"agm_{ref}"]

        d["margin_actual"] = d["margin_YTD"]
        d["margin_ref"] = d[f"margin_{ref}"]

        d["sgm_actual"] = d["sgm_ACT"]
        d["sgm_ref"] = d[f"sgm_{ref}"]

        d["Δ_SGM"] = d["sgm_actual"] - d["sgm_ref"]

        d["Actual SGM"] = d["sgm_actual"].apply(euro)
        d[f"SGM {ref}"] = d["sgm_ref"].apply(euro)

        d["Δ SGM"] = d["Δ_SGM"].apply(euro)

        # ===== DELTA =====
        d["Δ_TN_abs"] = d["tn_actual"] - d["tn_ref"]
        d["Δ_margin"] = (d["margin_actual"] - d["margin_ref"]) * 100

        # ===== FORMAT =====
        d["Actual TN"] = d["tn_actual"].apply(euro)
        d[f"{ref} TN"] = d["tn_ref"].apply(euro)

        d["Actual AGM"] = d["agm_actual"].apply(euro)
        d[f"{ref} AGM"] = d["agm_ref"].apply(euro)

        d["Margin Actual"] = d["margin_actual"].apply(lambda x: f"{x*100:.1f}%")
        d[f"Margin {ref}"] = d["margin_ref"].apply(lambda x: f"{x*100:.1f}%")

        d["Δ TN"] = d["Δ_TN_abs"].apply(euro)
        d["Δ Margin"] = d["Δ_margin"].apply(lambda x: f"{x:+.1f} pp")

        # ===== INSIGHT =====
        def insight(row):
            tn = row["Δ_TN_abs"]
            m = row["Δ_margin"]

            if pd.isna(tn) or pd.isna(m):
                return ""

            if m > 0 and tn > 0:
                return "Margin ↑ & Volume ↑"
            elif m > 0 and tn < 0:
                return "Margin ↑ & Volume ↓"
            elif m < 0 and tn > 0:
                return "Margin ↓ & Volume ↑"
            elif m < 0 and tn < 0:
                return "Margin ↓ & Volume ↓"

            return ""

        d["Insight"] = d.apply(insight, axis=1)

        d = d.sort_values("Δ_margin", ascending=True)

        return d[[
            "customer",
            "Actual TN", f"{ref} TN",
            "Actual AGM", f"{ref} AGM",
            "Actual SGM", f"SGM {ref}",
            "Δ TN", "Δ Margin", "Δ SGM",
            "Insight"
        ]]


    def highlight_problem(val):

        if "↑ & Volume ↑" in val:
            return "color: green; font-weight: bold;"

        elif "↑ & Volume ↓" in val:
            return "color: orange;"

        elif "↓ & Volume ↑" in val:
            return "color: orange;"

        elif "↓ & Volume ↓" in val:
            return "color: red; font-weight: bold;"

        return ""


    # ===== BDG TABLE =====
    with col1:
        st.markdown("### 💰 Vs Budget (RunRate Ranking)")
        df_bdg = build_analysis(pivot, "BDG")

        st.dataframe(
            df_bdg.style
                .map(highlight_delta, subset=["Δ TN", "Δ Margin"])
                .map(highlight_problem, subset=["Insight"]),
            use_container_width=True,
            height=500
        )


    # ===== FCS TABLE =====
    with col2:
        st.markdown("### 🔮 Vs Forecast (RunRate Ranking)")
        df_fcs = build_analysis(pivot, "FCS1")

        
        st.dataframe(
            df_fcs.style
                .map(highlight_delta, subset=["Δ TN", "Δ Margin"])
                .map(highlight_problem, subset=["Insight"]),
            use_container_width=True,
            height=500
        )

    st.markdown("---")
    st.markdown("## 📊 Actual Performance Analysis")

    col1, col2 = st.columns(2)

    # ===== BDG ACTUAL =====
    with col1:
        st.markdown("### 💰 Vs Budget (Actual Ranking)")

        df_bdg_act = build_analysis_actual(pivot, "BDG")

        st.dataframe(
            df_bdg_act.style
                .map(highlight_delta, subset=["Δ TN", "Δ Margin"])
                .map(highlight_problem, subset=["Insight"]),
            use_container_width=True,
            height=500
        )

    # ===== FCS ACTUAL =====
    with col2:
        st.markdown("### 🔮 Vs Forecast (Actual Ranking)")

        df_fcs_act = build_analysis_actual(pivot, "FCS1")

        st.dataframe(
            df_fcs_act.style
                .map(highlight_delta, subset=["Δ TN", "Δ Margin"])
                .map(highlight_problem, subset=["Insight"]),
            use_container_width=True,
            height=500
        )

