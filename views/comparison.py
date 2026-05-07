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
# LOAD DATA (✅ FIXED)
# ==================================================
@st.cache_data
def load_data():

    def load_file(path, scenario):
        df = pd.read_excel(path)
        df = clean_columns(df)

        df = df.rename(columns={

            # common
            "CUSTOMER MERGE": "customer",
            "PRODUCT": "product",
            "PN ALLESTIMENTO": "pn",

            # ✅ UNITS
            "ACT UNITS": "units",
            "UNITS": "units",
            "FY UNITS": "units",

            # ✅ TN
            "ACT TN": "tn",
            "TN": "tn",
            "FY TN": "tn",

            # ✅ COGS
            "ACT COGS": "cogs",
            "COGS": "cogs",
            "FY COGS": "cogs",

            # ✅ AGM
            "ACT AGM": "agm",
            "AGM": "agm",

            # ✅ SGM
            "ACT SGM": "sgm",
            "SGM": "sgm"
        })

        df["SCENARIO"] = scenario
        return df

    march = load_file(BASE_PATH / "raw_agm03.xlsx", "MARCH")
    feb = load_file(BASE_PATH / "raw_agm02.xlsx", "FEB")
    bdg = load_file(BASE_PATH / "raw_bdg26.xlsx", "BDG")
    fcst = load_file(BASE_PATH / "raw_fcs1_26.xlsx", "FCST")

    df = pd.concat([march, feb, bdg, fcst])

    for c in ["units", "tn", "cogs", "agm", "sgm"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    return df


# ==================================================
# PAGE
# ==================================================
def render_comparison():

    st.title("📊 Scenario Comparison")

    df = load_data()

    # ==================================================
    # FILTER
    # ==================================================
    customers = st.multiselect(
        "Customer",
        sorted(df["customer"].dropna().unique())
    )

    if not customers:
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
    # SCENARIOS
    # ==================================================
    scenarios = df["SCENARIO"].unique()

    col1, col2, col3 = st.columns(3)

    with col1:
        scenario_A = st.selectbox("Scenario A", scenarios)

    with col2:
        scenario_B = st.selectbox("Scenario B", scenarios)
    with col3:
        scenario_C = st.selectbox(
            "Optional Scenario (Reference)",
            ["None"] + list(scenarios)
        )


    if scenario_C != "None":
        st.caption(f"A = {scenario_A} | B = {scenario_B} | Reference = {scenario_C}")
    else:
        st.caption(f"A = {scenario_A} | B = {scenario_B}")
    # ==================================================
    # METRICS (✅ USER FRIENDLY)
    # ==================================================
    metric_map = {
        "Units": "units",
        "Turnover (TN)": "tn",
        "Gross Margin (AGM)": "agm",
        "Cost (COGS)": "cogs", 
        "Standard Margin (SGM)": "sgm"
    }

    metrics_ui = st.multiselect(
        "Metrics",
        list(metric_map.keys()),
        default=["Turnover (TN)", "Gross Margin (AGM)"]
    )

    if not metrics_ui:
        st.stop()

    metrics = [metric_map[m] for m in metrics_ui]

    # ==================================================
    # AGGREGATE
    # ==================================================
    df_group = df.groupby(
        group_cols + ["SCENARIO"],
        as_index=False
    )[metrics].sum()

    pivot = df_group.pivot(
        index=group_cols,
        columns="SCENARIO"
    )

    pivot.columns = [f"{c[1]}_{c[0]}" for c in pivot.columns]
    pivot = pivot.reset_index()

    # ==================================================
    # CALCULATIONS
    # ==================================================
    for m in metrics:

        col_A = f"{scenario_A}_{m}"
        col_B = f"{scenario_B}_{m}"

        if col_A in pivot.columns and col_B in pivot.columns:

            pivot[f"Δ {m.upper()} (A-B)"] = pivot[col_A] - pivot[col_B]

            pivot[f"%Δ {m.upper()}"] = (
                pivot[f"Δ {m.upper()} (A-B)"] / pivot[col_B]
            ).replace([float("inf"), -float("inf")], 0) * 100


    # ✅ ✅ BURAYA KOY
    if scenario_C != "None":
        for m in metrics:
            col_C = f"{scenario_C}_{m}"
            if col_C in pivot.columns:
                pass  # zaten var, dokunma


    # ✅ MARGIN
    if "agm" in metrics and "tn" in metrics:

        pivot[f"{scenario_A}_AGM % (AGM/TN)"] = (
            pivot[f"{scenario_A}_agm"] / pivot[f"{scenario_A}_tn"]
        ) * 100

        pivot[f"{scenario_B}_AGM % (AGM/TN)"] = (
            pivot[f"{scenario_B}_agm"] / pivot[f"{scenario_B}_tn"]
        ) * 100

    pivot = pivot.fillna(0)
    # ==================================================
# TOTAL ROW ✅
# ==================================================

# numeric kolonları al
    total = pivot.select_dtypes(include="number").sum()

    # ✅ MARGIN'ları tekrar hesapla (çok önemli)
    if f"{scenario_A}_AGM % (AGM/TN)" in pivot.columns:
        if f"{scenario_A}_tn" in total and total[f"{scenario_A}_tn"] != 0:
            total[f"{scenario_A}_AGM % (AGM/TN)"] = (
                total[f"{scenario_A}_agm"] / total[f"{scenario_A}_tn"]
            ) * 100

    if f"{scenario_B}_AGM % (AGM/TN)" in pivot.columns:
        if f"{scenario_B}_tn" in total and total[f"{scenario_B}_tn"] != 0:
            total[f"{scenario_B}_AGM % (AGM/TN)"] = (
                total[f"{scenario_B}_agm"] / total[f"{scenario_B}_tn"]
            ) * 100

    # ✅ group kolonlarını ekle
    for col in group_cols:
        total[col] = "TOTAL"

    # dataframe yap
    total_df = pd.DataFrame([total])

    # kolonları hizala
    total_df = total_df.reindex(columns=pivot.columns, fill_value="")

    # append
    pivot = pd.concat([pivot, total_df], ignore_index=True)
        # ✅ C scenario’yu da ekle
    

    ordered_cols = group_cols.copy()

    for m in metrics:
        col_A = f"{scenario_A}_{m}"
        col_B = f"{scenario_B}_{m}"
        col_C = f"{scenario_C}_{m}"

        if col_A in pivot.columns:
            ordered_cols.append(col_A)

        if col_B in pivot.columns:
            ordered_cols.append(col_B)

        if scenario_C != "None" and col_C in pivot.columns:
            ordered_cols.append(col_C)

        delta_col = f"Δ {m.upper()} (A-B)"
        pct_col = f"%Δ {m.upper()}"

        if delta_col in pivot.columns:
            ordered_cols.append(delta_col)

        if pct_col in pivot.columns:
            ordered_cols.append(pct_col)

    # ✅✅ EN KRİTİK SATIR → SADECE BURADA OLACAK
    # ✅ duplicate kolonları temizle
    ordered_cols = list(dict.fromkeys(ordered_cols))
    pivot = pivot[ordered_cols]
   # ==================================================
    # DISPLAY
    # ==================================================
    st.subheader("Results")

    def highlight_total(row):
        if row.iloc[0] == "TOTAL":
            return ["background-color: #d9edf7"] * len(row)
        return [""] * len(row)
    
    def highlight_delta(val):
        try:
            if float(val) > 0:
                return "color: green"
            elif float(val) < 0:
                return "color: red"
        except:
            return ""
        return ""





    st.dataframe(pivot, use_container_width=True)


    st.caption("""
    Δ = Difference between Scenario A and B  
    %Δ = Relative change ((A-B)/B)  
    AGM% = Profitability (AGM / TN)
    """)
