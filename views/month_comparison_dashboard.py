import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path



BASE_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "clean excel files"
)

MONTH_FILES = {
    "Apr-26": BASE_PATH / "c04_2026_clean.xlsx",
    "May-26": BASE_PATH / "c05_2026_clean.xlsx",
}

REFERENCE_FILES = {
    "BDG": BASE_PATH / "BDG2026_v4_clean.xlsx",
    "LY": BASE_PATH / "LY25_clean.xlsx",
    "FCST1": BASE_PATH / "fcst1_2026_clean.xlsx",
}

# =====================================================
# COLUMN CLEANER
# =====================================================

def clean_columns(df):

    df.columns = (
        df.columns.astype(str)
        .str.replace("\n", " ")
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
        .str.upper()
    )

    return df


# =====================================================
# STANDARDIZE
# =====================================================

def standardize(df):

    df = clean_columns(df)

    rename_map = {
        "CUSTOMER MERGE": "customer_merge",
        "FAMILY": "family",
        "PRODUCT": "product",
        "PLANT": "plant",
        "PN ALLESTIMENTO": "pn_allestimento",
        "UNITS": "units",
        "TN": "tn",
        "COGS": "cogs",
        "VCE": "vce",
        "SGM": "sgm",
        "AGM": "agm"
    }

    df = df.rename(columns=rename_map)

    required_cols = [
        "customer_merge",
        "family",
        "product",
        "plant",
        "pn_allestimento",
        "units",
        "tn",
        "cogs",
        "vce",
        "sgm",
        "agm"
    ]

    for col in required_cols:

        if col not in df.columns:

            if col in [
                "customer_merge",
                "family",
                "product",
                "plant",
                "pn_allestimento"
            ]:
                df[col] = "UNKNOWN"
            else:
                df[col] = 0

    numeric_cols = [
        "units",
        "tn",
        "cogs",
        "vce",
        "sgm",
        "agm"
    ]

    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    df["customer_merge"] = (
        df["customer_merge"]
        .astype(str)
        .str.strip()
        .str.upper()
    )
    customer_mapping = {
        "SDF": "SAME DEUTZ-FAHR DEUTSCHLAND GMBH",
        "ATLAS COPCO_NC": "ATLAS COPCO",
        "YANMAR ITALY": "YANMAR"
    }
    df["customer_merge"] = (
        df["customer_merge"]
        .replace(customer_mapping)
    )
    family_mapping = {
            "ATS": "LOOSE PARTS",
        }
    df["family"] = (
        df["family"]
        .astype(str)
        .str.strip()
        .replace(family_mapping)
    )
    
    product_mapping = {
            "ATS": "LOOSE PARTS",
        }
    df["product"] = (
        df["product"]
        .astype(str)
        .str.strip()
        .replace(product_mapping)
    )
    pn_allestimento_mapping = {
            "ATS": "LOOSE PARTS",   
        }
    df["pn_allestimento"] = (
        df["pn_allestimento"]
        .fillna("UNKNOWN")
        .astype(str)
        .replace(["nan", "NaN", "None"], "UNKNOWN")
        .str.replace(".0", "", regex=False)
        .str.strip()
        .replace(pn_allestimento_mapping)
    )

    return df


# =====================================================
# LOAD ALL DATA
# =====================================================

@st.cache_data
def load_all_data():

    all_frames = []

    # -------------------------
    # MONTH FILES
    # -------------------------

    for month_name, file_path in MONTH_FILES.items():

        try:

            df = pd.read_excel(file_path)

            df = standardize(df)

            df["scenario"] = month_name

            all_frames.append(df)

        except Exception as e:

            st.warning(f"{month_name} could not be loaded: {e}")

    # -------------------------
    # BDG / LY / FCST
    # -------------------------

    for scen, file_path in REFERENCE_FILES.items():

        try:

            df = pd.read_excel(file_path)

            df = standardize(df)

            df["scenario"] = scen

            all_frames.append(df)

        except Exception as e:

            st.warning(f"{scen} could not be loaded: {e}")

    if len(all_frames) == 0:
        return pd.DataFrame()

    df = pd.concat(all_frames, ignore_index=True)

    return df


# =====================================================
# ENRICH
# =====================================================

def enrich(df):

    df = df.copy()

    df["var"] = (
        df.get("tn", 0)
        - df.get("cogs", 0)
        - df.get("vce", 0)
        - df.get("agm", 0)
    )

    df["price"] = np.where(
        df["units"] != 0,
        df.get("tn", 0) / df["units"],
        0
    )

    df["cost"] = np.where(
        df["units"] != 0,
        df.get("cogs", 0) / df["units"],
        0
    )

    df["agm_pct"] = np.where(
        df["tn"] != 0,
        df["agm"] / df["tn"] * 100,
        0
    )

    df["sgm_pct"] = np.where(
        df["tn"] != 0,
        df["sgm"] / df["tn"] * 100,
        0
    )

    return df


# =====================================================
# FORMATTING
# =====================================================

def human_format(x):

    if pd.isna(x):
        return ""

    x = float(x)

    if abs(x) >= 1_000_000:
        return f"{x/1_000_000:.1f}M"

    elif abs(x) >= 1_000:
        return f"{x/1_000:.1f}K"

    return f"{x:,.0f}"


def euro(x):

    if pd.isna(x):
        return ""

    return f"€ {human_format(x)}"


def pct(x):

    if pd.isna(x):
        return ""

    return f"{x:.1f}%"


def pp(x):

    if pd.isna(x):
        return ""

    return f"{x:+.1f} pp"


def units_fmt(x):

    if pd.isna(x):
        return ""

    return f"{int(round(x)):,}"


# =====================================================
# KPI LIST
# =====================================================

BASE_KPIS = [
    "units",
    "tn",
    "var",
    "price",
    "cost",
    "agm",
    "agm_pct",
    "sgm",
    "sgm_pct"
]
# =====================================================
# BUILD EXECUTIVE SUMMARY
# =====================================================

def build_summary_table(
    df,
    level_cols,
    base_scenario,
    compare_scenarios,
    selected_kpis
):

    all_scenarios = [base_scenario] + compare_scenarios

    work = df[df["scenario"].isin(all_scenarios)].copy()

    agg = (
        work.groupby(
            level_cols + ["scenario"],
            as_index=False
        )[[
            "units",
            "tn",

            "agm",
            "sgm",
            "cogs",
            "vce"
        ]]
        .sum()
    )

    agg = enrich(agg)

    pivot = agg.pivot_table(
        index=level_cols,
        columns="scenario",
        values=selected_kpis,
        fill_value=0
    )

    pivot.columns = [
        f"{k}_{s}"
        for k, s in pivot.columns
    ]

    pivot = pivot.reset_index()

    # ====================================
    # DELTAS
    # ====================================

    for comp in compare_scenarios:

        mappings = [
            ("units", False),
            ("tn", False),
            ("var", False),
            ("price", False),
            ("cost", False),
            ("agm", False),
            ("sgm", False),
            ("agm_pct", True),
            ("sgm_pct", True),
        ]

        for metric, is_pct in mappings:

            base_col = f"{metric}_{base_scenario}"
            comp_col = f"{metric}_{comp}"

            if (
                base_col in pivot.columns
                and comp_col in pivot.columns
            ):

                pivot[f"Δ_{metric}_vs_{comp}"] = (
                    pivot[base_col]
                    - pivot[comp_col]
                )





    ordered_cols = level_cols.copy()

    for metric in selected_kpis:

        base_col = f"{metric}_{base_scenario}"

        if base_col in pivot.columns:
            ordered_cols.append(base_col)

        for comp in compare_scenarios:

            comp_col = f"{metric}_{comp}"
            delta_col = f"Δ_{metric}_vs_{comp}"

            if comp_col in pivot.columns:
                ordered_cols.append(comp_col)

            if delta_col in pivot.columns:
                ordered_cols.append(delta_col)

    pivot = pivot[
        [c for c in ordered_cols if c in pivot.columns]
    ]

    return pivot


# =====================================================
# FORMAT SUMMARY TABLE
# =====================================================

def format_summary_table(df):

    out = df.copy()

    for col in out.columns:

        if col.startswith("Δ_agm_pct"):
            out[col] = out[col].apply(pp)

        elif col.startswith("Δ_sgm_pct"):
            out[col] = out[col].apply(pp)

        elif col.startswith("agm_pct_"):
            out[col] = out[col].apply(pct)

        elif col.startswith("sgm_pct_"):
            out[col] = out[col].apply(pct)

        elif col.startswith("Δ_units"):
            out[col] = out[col].apply(units_fmt)

        elif col.startswith("units_"):
            out[col] = out[col].apply(units_fmt)

        elif (
            col.startswith("tn_")
            or col.startswith("agm_")
            or col.startswith("sgm_")
            or col.startswith("var_")
            or col.startswith("price_")
            or col.startswith("cost_")
            or col.startswith("Δ_var")
            or col.startswith("Δ_price")
            or col.startswith("Δ_cost")
        ):
            out[col] = out[col].apply(euro)

    return out


# =====================================================
# HTML DELTA COLOR
# =====================================================
def highlight_summary(df):

    df = df.copy()

    reverse_metrics = [
        "cost",
        "cogs",
        "var"
    ]

    for col in df.columns:

        if not col.startswith("Δ"):
            continue

        is_reverse = any(
            m in col.lower()
            for m in reverse_metrics
        )

        def colorize(v):

            txt = str(v)

            try:
                num = float(
                    txt
                    .replace("€","")
                    .replace("M","")
                    .replace("K","")
                    .replace("pp","")
                    .replace("%","")
                    .replace(",","")
                    .strip()
                )
            except:
                return txt

            if is_reverse:

                if num > 0:
                    color = "red"

                elif num < 0:
                    color = "green"

                else:
                    color = "black"

            else:

                if num > 0:
                    color = "green"

                elif num < 0:
                    color = "red"

                else:
                    color = "black"

            return (
                f"<span style='color:{color};font-weight:bold'>"
                f"{txt}"
                f"</span>"
            )

        df[col] = df[col].apply(colorize)

    return df
def highlight_unit_table(df):

    delta_cols = [
        c
        for c in df.columns
        if str(c).startswith("Δ")
    ]

    if not delta_cols:
        return df.style

    def colorize(v):

        try:
            num = float(v)
        except:
            return ""

        if num > 0:
            return "color:green;font-weight:bold;"
        elif num < 0:
            return "color:red;font-weight:bold;"

        return ""

    return df.style.map(
        colorize,
        subset=delta_cols
    )
# =====================================================
# FILTER AREA
# =====================================================

def render_filters(df):

    st.subheader("filters")

    available_scenarios = (
        sorted(df["scenario"].dropna().unique())
    )

    default_base = (
        "May-26"
        if "May-26" in available_scenarios
        else available_scenarios[0]
    )

    base_scenario = st.selectbox(
        "Base Scenario",
        available_scenarios,
        index=available_scenarios.index(default_base)
    )

    compare_scenarios = st.multiselect(
        "Compare Against",
        [s for s in available_scenarios if s != base_scenario],
        default=[
            s
            for s in ["Apr-26", "BDG", "LY", "FCST1"]
            if (
                s in available_scenarios
                and s != base_scenario
            )
        ]
    )

    customers = st.multiselect(
        "Customer",
        sorted(df["customer_merge"].dropna().unique())
    )

    families = st.multiselect(
        "Family",
        sorted(df["family"].dropna().unique())
    )

    products = st.multiselect(
        "Product",
        sorted(df["product"].dropna().unique())
    )

    pns = st.multiselect(
        "PN",
        sorted(df["pn_allestimento"].dropna().unique())
    )

    filtered = df.copy()

    if customers:
        filtered = filtered[
            filtered["customer_merge"].isin(customers)
        ]

    if families:
        filtered = filtered[
            filtered["family"].isin(families)
        ]

    if products:
        filtered = filtered[
            filtered["product"].isin(products)
        ]

    if pns:
        filtered = filtered[
            filtered["pn_allestimento"].isin(pns)
        ]


    selected_kpis = st.multiselect(
        "KPIs",
        [
            "units",
            "tn",
            "var",
            "price",
            "cost",
            "agm",
            "agm_pct",
            "sgm",
            "sgm_pct"
        ],
)

    return (
        filtered,
        base_scenario,
        compare_scenarios,
        selected_kpis
    )


# =====================================================
# EXECUTIVE SECTION
# =====================================================

def render_executive_section(
    df,
    base_scenario,
    compare_scenarios,
    selected_kpis
):

    st.header("Executive Summary")

    summary = build_summary_table(
        df=df,
        level_cols=["customer_merge"],
        base_scenario=base_scenario,
        compare_scenarios=compare_scenarios,
        selected_kpis=selected_kpis
    )

    primary_sort = None

    if selected_kpis and compare_scenarios:

        first_kpi = selected_kpis[0]
        first_comp = compare_scenarios[0]

        candidate = f"Δ_{first_kpi}_vs_{first_comp}"

        if candidate in summary.columns:
            primary_sort = candidate

    if primary_sort:

        summary = summary.sort_values(
            by=primary_sort,
            ascending=True,
            na_position="last"
        )
    display_df = format_summary_table(summary)
    display_df = display_df.rename(
        columns={
            "customer_merge": "Customer"
        }
    )

    display_df.columns = [
        c.replace("agm_", "AGM ")
        .replace("agm_pct_", "AGM % ")
        .replace("tn_", "TN ")
        .replace("units_", "Units ")
        .replace("sgm_", "SGM ")
        .replace("sgm_pct_", "SGM % ")
        .replace("Δ_agm_vs_", "Δ AGM vs ")
        .replace("Δ_agm_pct_vs_", "Δ AGM % vs ")
        .replace("Δ_tn_vs_", "Δ TN vs ")
        .replace("Δ_units_vs_", "Δ Units vs ")
        .replace("Δ_sgm_vs_", "Δ SGM vs ")
        .replace("Δ_sgm_pct_vs_", "Δ SGM % vs ")
        .replace("var_", "VAR ")
        .replace("price_", "PRICE ")
        .replace("cost_", "COST ")

        .replace("Δ_var_vs_", "Δ VAR vs ")
        .replace("Δ_price_vs_", "Δ PRICE vs ")
        .replace("Δ_cost_vs_", "Δ COST vs ")
        for c in display_df.columns
    ]

    st.markdown(
        highlight_summary(display_df)
        .to_html(
            escape=False,
            index=False
        ),
        unsafe_allow_html=True
    )

    return summary
# =====================================================
# DETAIL TABLE
# =====================================================

LEVEL_MAP = {
    "Customer": ["customer_merge"],
    "Family": ["customer_merge", "family"],
    "Product": ["customer_merge", "family", "product"],
    "PN": [
        "customer_merge",
        "family",
        "product",
        "plant",
        "pn_allestimento"
    ]
}


def build_detail_table(
    df,
    level,
    base_scenario,
    compare_scenarios,
    selected_kpis
):

    group_cols = LEVEL_MAP[level]

    scenarios = [base_scenario] + compare_scenarios

    work = df[
        df["scenario"].isin(scenarios)
    ].copy()

    agg = (
        work.groupby(
            group_cols + ["scenario"],
            as_index=False
        )[[
            "units",
            "tn",
            "agm",
            "sgm",
            "cogs",
            "vce"
        ]]
        .sum()
    )

    agg = enrich(agg)

    detail = agg.pivot_table(
        index=group_cols,
        columns="scenario",
        values=selected_kpis,
        fill_value=0
    )

    detail.columns = [
        f"{m}_{s}"
        for m, s in detail.columns
    ]

    detail = detail.reset_index()

    # ====================================
    # DELTAS
    # ====================================

    metrics = [
        "units",
        "tn",
        "var",
        "price",
        "cost",
        "agm",
        "sgm",
        "agm_pct",
        "sgm_pct"
    ]

    for comp in compare_scenarios:

        for metric in metrics:

            base_col = f"{metric}_{base_scenario}"
            comp_col = f"{metric}_{comp}"

            if (
                base_col in detail.columns
                and comp_col in detail.columns
            ):

                detail[
                    f"Δ_{metric}_vs_{comp}"
                ] = (
                    detail[base_col]
                    - detail[comp_col]
                )
    ordered_cols = group_cols.copy()

    for metric in selected_kpis:

        base_col = f"{metric}_{base_scenario}"

        if base_col in detail.columns:
            ordered_cols.append(base_col)

        for comp in compare_scenarios:

            comp_col = f"{metric}_{comp}"
            delta_col = f"Δ_{metric}_vs_{comp}"

            if comp_col in detail.columns:
                ordered_cols.append(comp_col)

            if delta_col in detail.columns:
                ordered_cols.append(delta_col)

    detail = detail[
        [c for c in ordered_cols if c in detail.columns]
    ]
    return detail


# =====================================================
# DETAIL TABLE FORMAT
# =====================================================

def format_detail_table(df):

    out = df.copy()

    for col in out.columns:

        if "agm_pct" in col:
            if col.startswith("Δ_"):
                out[col] = out[col].apply(pp)
            else:
                out[col] = out[col].apply(pct)

        elif "sgm_pct" in col:
            if col.startswith("Δ_"):
                out[col] = out[col].apply(pp)
            else:
                out[col] = out[col].apply(pct)

        elif "units" in col:
            if not col.startswith("customer"):
                out[col] = out[col].apply(units_fmt)

        elif (
            col.startswith("tn_")
            or col.startswith("agm_")
            or col.startswith("sgm_")
            or col.startswith("var_")
            or col.startswith("price_")
            or col.startswith("cost_")
            or col.startswith("Δ_var")
            or col.startswith("Δ_price")
            or col.startswith("Δ_cost")
        ):
            out[col] = out[col].apply(euro)

    return out


# =====================================================
# DETAIL SECTION
# =====================================================

def render_detail_section(
    df,
    base_scenario,
    compare_scenarios,
    selected_kpis
):

    st.header("Detail Analysis")

    level = st.selectbox(
        "Aggregation Level",
        [
            "Customer",
            "Family",
            "Product",
            "PN"
        ]
    )

    detail = build_detail_table(
        df=df,
        level=level,
        base_scenario=base_scenario,
        compare_scenarios=compare_scenarios,
        selected_kpis=selected_kpis
    )

    sort_options = [
        c
        for c in detail.columns
        if c.startswith("Δ_")
    ]


    if len(sort_options):

        sort_col = st.selectbox(
            "Sort By",
            sort_options
        )

        detail = detail.sort_values(
            sort_col,
            ascending=True
        )

    display_df = format_detail_table(detail)

    st.markdown(
        highlight_summary(display_df)
        .to_html(
            escape=False,
            index=False
        ),
        unsafe_allow_html=True
    )

    return detail
# =====================================================
# UNIT ECONOMICS
# =====================================================

def build_unit_table(
    df,
    level,
    base_scenario,
    compare_scenarios
):

    group_cols = LEVEL_MAP[level]

    scenarios = [base_scenario] + compare_scenarios

    work = df[
        df["scenario"].isin(scenarios)
    ].copy()

    agg = (
        work.groupby(
            group_cols + ["scenario"],
            as_index=False
        )[[
            "units",
            "tn",
            "agm",
            "sgm",
            "cogs",
            "vce"
        ]]
        .sum()
    )
    
    agg["var"] = (
        agg["tn"]
        - agg["cogs"]
        - agg["vce"]
        - agg["agm"]
    )

    agg["price"] = np.where(
        agg["units"] != 0,
        agg["tn"] / agg["units"],
        0
    )

    agg["cost"] = np.where(
        agg["units"] != 0,
        agg["cogs"] / agg["units"],
        0
    )
    for metric in ["tn", "cogs", "vce", "agm", "sgm"]:

        agg[f"{metric}_unit"] = np.where(
            agg["units"] != 0,
            agg[metric] / agg["units"],
            0
        )

    unit_tbl = agg.pivot_table(
        index=group_cols,
        columns="scenario",
        values=[
            "price",
            "cost",
            "var",
            "tn_unit",
            "cogs_unit",
            "vce_unit",
            "agm_unit",
            "sgm_unit"
        ],
        fill_value=0
    )

    unit_tbl.columns = [
        f"{m}_{s}"
        for m, s in unit_tbl.columns
    ]

    metrics = [
        "price",
        "cost",
        "var",
        "tn_unit",
        "cogs_unit",
        "vce_unit",
        "agm_unit",
        "sgm_unit"
    ]

    unit_tbl = unit_tbl.reset_index()

    for comp in compare_scenarios:

        for metric in metrics:

            base_col = f"{metric}_{base_scenario}"
            comp_col = f"{metric}_{comp}"

            if (
                base_col in unit_tbl.columns
                and comp_col in unit_tbl.columns
            ):

                unit_tbl[f"Δ_{metric}_vs_{comp}"] = (
                    unit_tbl[base_col]
                    - unit_tbl[comp_col]
                )

    ordered_cols = group_cols.copy()

    for metric in metrics:

        base_col = f"{metric}_{base_scenario}"

        if base_col in unit_tbl.columns:
            ordered_cols.append(base_col)

        for comp in compare_scenarios:

            comp_col = f"{metric}_{comp}"
            delta_col = f"Δ_{metric}_vs_{comp}"

            if comp_col in unit_tbl.columns:
                ordered_cols.append(comp_col)

            if delta_col in unit_tbl.columns:
                ordered_cols.append(delta_col)

    unit_tbl = unit_tbl[
        [c for c in ordered_cols if c in unit_tbl.columns]
    ]

    unit_tbl.columns = [
        str(c)
        .replace("price_", "PRICE ")
        .replace("cost_", "COST ")
        .replace("var_", "VAR ")
        .replace("tn_unit_", "TN/unit ")
        .replace("cogs_unit_", "COGS/unit ")
        .replace("vce_unit_", "VCE/unit ")
        .replace("agm_unit_", "AGM/unit ")
        .replace("sgm_unit_", "SGM/unit ")

        .replace("Δ_price_vs_", "Δ PRICE vs ")
        .replace("Δ_cost_vs_", "Δ COST vs ")
        .replace("Δ_var_vs_", "Δ VAR vs ")

        .replace("Δ_tn_unit_vs_", "Δ TN/unit vs ")
        .replace("Δ_cogs_unit_vs_", "Δ COGS/unit vs ")
        .replace("Δ_vce_unit_vs_", "Δ VCE/unit vs ")
        .replace("Δ_agm_unit_vs_", "Δ AGM/unit vs ")
        .replace("Δ_sgm_unit_vs_", "Δ SGM/unit vs ")

        for c in unit_tbl.columns
    ]


    return unit_tbl


# =====================================================
# DRIVER ANALYSIS
# =====================================================

def build_driver_table(
    df,
    level_col,
    base_scenario,
    compare_scenario
):

    work = df[
        df["scenario"].isin(
            [base_scenario, compare_scenario]
        )
    ].copy()

    grp = (
        work.groupby(
            [level_col, "scenario"],
            as_index=False
        )["agm"]
        .sum()
    )

    p = grp.pivot_table(
        index=level_col,
        columns="scenario",
        values="agm",
        fill_value=0
    ).reset_index()

    if (
        base_scenario not in p.columns
        or compare_scenario not in p.columns
    ):
        return pd.DataFrame()

    p["Δ_agm"] = (
        p[base_scenario]
        - p[compare_scenario]
    )

    return p.sort_values(
        "Δ_agm",
        ascending=True
    )


# =====================================================
# DRIVER SECTION
# =====================================================

def render_driver_section(
    df,
    base_scenario,
    compare_scenarios,
    selected_kpis
):

    if len(compare_scenarios) == 0:
        return

    st.header("Drivers Analysis")

    compare_driver = st.selectbox(
        "Driver Comparison",
        compare_scenarios
    )

    level_driver = st.selectbox(
        "Driver Level",
        [
            "customer_merge",
            "family",
            "product",
            "pn_allestimento"
        ]
    )

    drv = build_driver_table(
        df,
        level_driver,
        base_scenario,
        compare_driver
    )

    if drv.empty:
        st.warning("No driver data")
        return

    worst = drv.head(10)
    best = drv.tail(10).sort_values(
        "Δ_agm",
        ascending=False
    )

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("🔴 Worst Drivers")

        tmp = worst.copy()
        tmp["Δ_agm"] = tmp["Δ_agm"].apply(euro)

        st.dataframe(
            tmp,
            width="stretch"
        )

    with col2:

        st.subheader("🟢 Best Drivers")

        tmp = best.copy()
        tmp["Δ_agm"] = tmp["Δ_agm"].apply(euro)

        st.dataframe(
            tmp,
            width="stretch"
        )


# =====================================================
# KPI CARDS
# =====================================================

def render_kpis(
    df,
    base_scenario
):

    base = df[
        df["scenario"] == base_scenario
    ]

    units = base["units"].sum()
    tn = base["tn"].sum()
    agm = base["agm"].sum()
    sgm = base["sgm"].sum()

    agm_pct = (
        agm / tn * 100
        if tn != 0
        else 0
    )

    sgm_pct = (
        sgm / tn * 100
        if tn != 0
        else 0
    )

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Units", units_fmt(units))
    c2.metric("TN", euro(tn))
    c3.metric("AGM", euro(agm))
    c4.metric("AGM %", pct(agm_pct))
    c5.metric("SGM %", pct(sgm_pct))


# =====================================================
# MAIN RENDER
# =====================================================

def render():

    st.set_page_config(
        layout="wide"
    )

    st.title(
        "📊 Multi Month Comparison Dashboard"
    )

    df = load_all_data()

    if df.empty:
        st.error("No data loaded")
        return

    df = enrich(df)

    (
        filtered_df,
        base_scenario,
        compare_scenarios,
        selected_kpis
    ) = render_filters(df)

    render_kpis(
        filtered_df,
        base_scenario
    )

    st.divider()

    render_executive_section(
        filtered_df,
        base_scenario,
        compare_scenarios,
        selected_kpis
    )

    st.divider()

    render_detail_section(
        filtered_df,
        base_scenario,
        compare_scenarios,
        selected_kpis
    )

    st.divider()

    st.header("Unit Economics")

    level = st.selectbox(
        "Unit View Level",
        list(LEVEL_MAP.keys()),
        key="unit_view_level"
    )

    unit_df = build_unit_table(
        filtered_df,
        level,
        base_scenario,
        compare_scenarios
    )

    styled_unit = highlight_unit_table(unit_df)

    st.dataframe(
        styled_unit,
        width="stretch"
    )




    st.divider()

    render_driver_section(
        filtered_df,
        base_scenario,
        compare_scenarios,
        selected_kpis
    )


# =====================================================
# START
# =====================================================

def render_month_comparison_dashboard():
    render()

if __name__ == "__main__":
    render()