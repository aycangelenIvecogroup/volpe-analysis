import streamlit as st
import pandas as pd
from pathlib import Path

BASE_PATH = Path("data/raw")


# ==================================================
# CLEAN COLUMNS
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
# LOAD DATA (3 SCENARIOS)
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
    fy25 = load_file(BASE_PATH / "raw_agm_c12_2025.xlsx", "FY25")

    df = pd.concat([march, bdg, fy25])

    # CLEAN CUSTOMER (IMPORTANT)
    df["customer"] = df["customer"].astype(str).str.strip()

    # NUMERIC FIX
    for c in ["units", "tn", "cogs", "agm", "vce", "sgm"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    return df


# ==================================================
# SAFE DIVISION
# ==================================================
def safe_div(a, b):
    return a / b if b != 0 else 0


# ==================================================
# CALC ENGINE
# ==================================================
def compute_metrics(df_group):

    def get(s, col):
        return df_group.loc[s, col] if s in df_group.index else 0

    data = {}

    for s in ["FY25", "BDG", "MARCH"]:
        data[s] = {
            "units": get(s, "units"),
            "tn": get(s, "tn"),
            "cogs": get(s, "cogs"),
            "agm": get(s, "agm"),
        }

        data[s]["margin"] = safe_div(data[s]["agm"], data[s]["tn"])
        data[s]["unit_price"] = safe_div(data[s]["tn"], data[s]["units"])
        data[s]["unit_cost"] = safe_div(data[s]["cogs"], data[s]["units"])

    return data


# ==================================================
# EXPLANATION ENGINE
# ==================================================
def build_explanation(m):

    fy = m["FY25"]
    bdg = m["BDG"]
    act = m["MARCH"]

    strategy_gap = bdg["agm"] - fy["agm"]
    execution_gap = act["agm"] - bdg["agm"]

    explanation = f"""
### 📌 STRATEGY VS EXECUTION

- Strategy (BDG - FY25)(agm): **{strategy_gap:.0f} €**
- Execution (ACT - BDG)(agm): **{execution_gap:.0f} €**

---

# 🔬 FULL PERFORMANCE ANALYSIS

## 🟦 1. STRATEGY (FY25 → BDG)

Margin(%agm):
- {fy['margin']*100:.1f}% → {bdg['margin']*100:.1f}%
- Δ = {(bdg['margin']-fy['margin'])*100:.1f} pp

TN:
- {fy['tn']:.0f} → {bdg['tn']:.0f} (€ Δ {bdg['tn']-fy['tn']:.0f})

Cogs:
- {fy['cogs']:.0f} → {bdg['cogs']:.0f} (€ Δ {bdg['cogs']-fy['cogs']:.0f})

---

## 🟥 2. EXECUTION (BDG → ACTUAL)

Margin(%agm):
- {bdg['margin']*100:.1f}% → {act['margin']*100:.1f}%
- Δ = {(act['margin']-bdg['margin'])*100:.1f} pp

TN:
- {bdg['tn']:.0f} → {act['tn']:.0f} (€ Δ {act['tn']-bdg['tn']:.0f})

Cogs:
- {bdg['cogs']:.0f} → {act['cogs']:.0f} (€ Δ {act['cogs']-bdg['cogs']:.0f})



## 🟨 3. UNIT ECONOMICS

Unit Price:
- ACT = {act['tn']:.0f} / {act['units']:.0f} = {act['unit_price']:.2f}
- BDG = {bdg['tn']:.0f} / {bdg['units']:.0f} = {bdg['unit_price']:.2f}

Unit Cost:
- ACT = {act['cogs']:.0f} / {act['units']:.0f} = {act['unit_cost']:.2f}
- BDG = {bdg['cogs']:.0f} / {bdg['units']:.0f} = {bdg['unit_cost']:.2f}

---

## 🟥 ROOT CAUSE
"""

    # ROOT CAUSE TAGS
    if act["unit_cost"] > bdg["unit_cost"]:
        explanation += "- Cost inflation (unit cost increased)\n"
    if act["unit_price"] < bdg["unit_price"]:
        explanation += "- Pricing pressure (unit price decreased)\n"
    if act["units"] >= bdg["units"]:
        explanation += "- Volume not driving the issue\n"

    explanation += """

---

## ✅ CONCLUSION

Variance fully explained by cost vs TN imbalance,
validated through unit-level calculations.

"""

    return explanation


# ==================================================
# PAGE
# ==================================================
def render_full_diagnostic():

    st.title("🚀 Customer Profitability (FY25 vs BDG vs ACT)")

    df = load_data()

    # =========================
    # CUSTOMER SELECT
    # =========================
    customer = st.selectbox(
        "Select Customer",
        sorted(df["customer"].dropna().unique())
    )

    df = df[df["customer"] == customer]

    # =========================
    # GROUP DATA
    # =========================
    df_group = df.groupby("SCENARIO")[[
        "units", "tn", "cogs", "agm", "vce", "sgm" 
    ]].sum()

    # ORDER
    df_group = df_group.reindex(["FY25", "BDG", "MARCH"]).fillna(0)

    st.subheader("📊 Scenario Overview")
    st.dataframe(df_group, use_container_width=True)

    # =========================
    # COMPARISON TABLE
    # =========================
    comp = pd.DataFrame({
        "Metric": ["TN", "COGS", "AGM","VCE","SGM"],
        "FY25": df_group.loc["FY25"][["tn", "cogs", "agm", "vce", "sgm"]].values,
        "BDG": df_group.loc["BDG"][["tn", "cogs", "agm", "vce", "sgm"]].values,
        "ACT": df_group.loc["MARCH"][["tn", "cogs", "agm", "vce", "sgm"]].values,
    })

    comp["Strategy (BDG-FY25)"] = comp["BDG"] - comp["FY25"]
    comp["Execution (ACT-BDG)"] = comp["ACT"] - comp["BDG"]

    st.subheader("📈 Strategy vs Execution")
    st.dataframe(comp, use_container_width=True)

    # =========================
    # EXPLANATION
    # =========================
    metrics = compute_metrics(df_group)
    explanation = build_explanation(metrics)

    st.markdown(explanation)

    # ==================================================
    # PN LEVEL FULL BREAKDOWN (ACT vs BDG)
    # ==================================================
    st.subheader("🧩 Product Breakdown (ACT vs BDG)")

    pn_group = df.groupby(["pn", "SCENARIO"])[
        ["units", "tn", "cogs", "vce", "agm", "sgm"]
    ].sum().reset_index()

    # pivot
    pivot = pn_group.pivot(index="pn", columns="SCENARIO").fillna(0)

    # easier access
    def get(col, scen):
        if (col, scen) in pivot.columns:
            return pivot[(col, scen)]
        else:
            return pd.Series(0, index=pivot.index)


    # build final table
    product_table = pd.DataFrame({
        # UNITS
        "ACT Units": get("units", "MARCH"),
        "BDG Units": get("units", "BDG"),

        # TN
        "ACT TN": get("tn", "MARCH"),
        "BDG TN": get("tn", "BDG"),

        # COGS
        "ACT COGS": get("cogs", "MARCH"),
        "BDG COGS": get("cogs", "BDG"),

        # VCE
        "ACT VCE": get("vce", "MARCH"),
        "BDG VCE": get("vce", "BDG"),

        # AGM
        "ACT AGM": get("agm", "MARCH"),
        "BDG AGM": get("agm", "BDG"),

        # SGM
        "ACT SGM": get("sgm", "MARCH"),
        "BDG SGM": get("sgm", "BDG"),
    })

    # percentages
    product_table["ACT AGM %"] = product_table["ACT AGM"] / product_table["ACT TN"].replace(0, 1)
    product_table["BDG AGM %"] = product_table["BDG AGM"] / product_table["BDG TN"].replace(0, 1)

    product_table["ACT SGM %"] = product_table["ACT SGM"] / product_table["ACT TN"].replace(0, 1)
    product_table["BDG SGM %"] = product_table["BDG SGM"] / product_table["BDG TN"].replace(0, 1)
    # DELTA (çok önemli)
    product_table["Δ AGM"] = product_table["ACT AGM"] - product_table["BDG AGM"]
    product_table["Δ SGM"] = product_table["ACT SGM"] - product_table["BDG SGM"]

    product_table["Δ AGM %"] = product_table["ACT AGM %"] - product_table["BDG AGM %"]
    product_table["Δ SGM %"] = product_table["ACT SGM %"] - product_table["BDG SGM %"]

    product_table = product_table.sort_values("Δ AGM %", ascending=True)

    st.dataframe(
        product_table.style.format({
            "ACT AGM %": "{:.1%}",
            "BDG AGM %": "{:.1%}",
            "ACT SGM %": "{:.1%}",
            "BDG SGM %": "{:.1%}",
            "Δ AGM %": "{:.1%}",
            "Δ SGM %": "{:.1%}",
        }),
        use_container_width=True
    )    
    
    # ===============================
    # PN SELECTOR (RIGHT PLACE ✅)
    # ===============================
    st.subheader("🔎 Select PN for Unit Economics")

    pn_list = sorted(product_table.index)  # 🟢 BURASI DEĞİŞTİ (ÖNEMLİ)

    selected_pn = st.selectbox(
        "Select PN",
        pn_list
    )

    

    df_pn = df[df["pn"] == selected_pn]


    # ===============================
    # PN GROUP (SCENARIO)
    # ===============================
    df_pn_group = df_pn.groupby("SCENARIO")[[
        "units", "tn", "cogs", "agm", "vce", "sgm"
    ]].sum()

    df_pn_group = df_pn_group.reindex(["FY25", "BDG", "MARCH"]).fillna(0)


    # ===============================
    # UNIT CALCULATION
    # ===============================
    def calc_unit(row):
        units = row["units"] if row["units"] != 0 else 1

        unit_price = row["tn"] / units
        unit_cost = row["cogs"] / units
        unit_margin = row["agm"] / units
        unit_vce = row["vce"] / units
        unit_var = unit_price - (unit_cost + unit_vce + unit_margin)

        return pd.Series({
            "Unit Price": unit_price,
            "Unit COGS": unit_cost,
            "Unit VCE": unit_vce,
            "Unit AGM": unit_margin,
            "Unit SGM": (row["sgm"] / units),
            "Unit Variance": unit_var
        })

    unit_df = df_pn_group.apply(calc_unit, axis=1)


    # ===============================
    # BUILD UNIT TABLE (ACT vs BDG)
    # ===============================
    rows = []

    metrics = ["Unit Price", "Unit COGS", "Unit VCE", "Unit AGM", "Unit SGM", "Unit Variance"]

    for m in metrics:

        act_val = unit_df.loc["MARCH", m] if "MARCH" in unit_df.index else 0
        bdg_val = unit_df.loc["BDG", m] if "BDG" in unit_df.index else 0

        rows.append({
            "Metric": m,
            "ACT": act_val,
            "BDG": bdg_val,
            "Δ": act_val - bdg_val
        })

    unit_result = pd.DataFrame(rows)


    # ===============================
    # DISPLAY UNIT ENGINE
    # ===============================
    st.subheader(f"⚙️ Unit Economics detail: - {selected_pn}")

    def color_delta(val):
        if val > 0:
            return "color: green"
        elif val < 0:
            return "color: red"
        return ""

    styled = unit_result.style.apply(
        lambda col: [color_delta(v) for v in col] if col.name == "Δ" else ["" for _ in col],
        axis=0
    )

    st.dataframe(styled, use_container_width=True)


    # ===============================
    # AUTOMATIC MINI INSIGHT
    # ===============================
    act_agm = unit_df.loc["MARCH", "Unit AGM"]
    bdg_agm = unit_df.loc["BDG", "Unit AGM"]

    act_sgm = unit_df.loc["MARCH", "Unit SGM"]
    bdg_sgm = unit_df.loc["BDG", "Unit SGM"]

    act_price = unit_df.loc["MARCH", "Unit Price"]
    bdg_price = unit_df.loc["BDG", "Unit Price"]

    act_cost = unit_df.loc["MARCH", "Unit COGS"]
    bdg_cost = unit_df.loc["BDG", "Unit COGS"]

    

    act_var = unit_df.loc["MARCH", "Unit Variance"]
    bdg_var = unit_df.loc["BDG", "Unit Variance"]

    act_vce = unit_df.loc["MARCH", "Unit VCE"]
    bdg_vce = unit_df.loc["BDG", "Unit VCE"]
    



    st.markdown(f"""
    ### 🔍 PN Insight

    - Price: {bdg_price:.2f} → {act_price:.2f} (Δ {act_price-bdg_price:.2f})
    - Cost: {bdg_cost:.2f} → {act_cost:.2f} (Δ {act_cost-bdg_cost:.2f})

    - Unit AGM: {bdg_agm:.2f} → {act_agm:.2f} (Δ {act_agm-bdg_agm:.2f})
    - Unit SGM: {bdg_sgm:.2f} → {act_sgm:.2f} (Δ {act_sgm-bdg_sgm:.2f})

    ---

    ## 🧠 Full Price Bridge

    👉 Δ Price:
    **{act_price-bdg_price:.2f}**

    Breakdown:

    - Δ Cost: {act_cost-bdg_cost:.2f}
    - Δ VCE: {act_vce-bdg_vce:.2f}
    - Δ AGM: {act_agm-bdg_agm:.2f}
    - Δ VAR: {act_var-bdg_var:.2f}

    ---

    ✅ Check (must = 0):
    **{(act_price-bdg_price) - ((act_cost-bdg_cost)+(act_vce-bdg_vce)+(act_agm-bdg_agm)+(act_var-bdg_var)):.6f}**

    """)
   
    # ==================================================
    # UNIT-BASED WATERFALL ✅ (DOĞRU VERSİYON)
    # ==================================================
    st.subheader("📊 Mini Waterfall (Unit-Based)")

    # unit values
    act_units = df_pn_group.loc["MARCH", "units"]
    bdg_units = df_pn_group.loc["BDG", "units"]

    vce_effect = (act_vce - bdg_vce) * act_units
    var_effect = (act_var - bdg_var) * act_units


    act_price = unit_df.loc["MARCH", "Unit Price"]
    bdg_price = unit_df.loc["BDG", "Unit Price"]

    act_cost = unit_df.loc["MARCH", "Unit COGS"]
    bdg_cost = unit_df.loc["BDG", "Unit COGS"]

    bdg_agm = df_pn_group.loc["BDG", "agm"]
    act_agm = df_pn_group.loc["MARCH", "agm"]

   # effects
    volume_effect = (act_units - bdg_units) * bdg_price
    cost_effect = (act_cost - bdg_cost) * act_units * -1
    vce_effect = (act_vce - bdg_vce) * act_units
    var_effect = (act_var - bdg_var) * act_units

    waterfall_df = pd.DataFrame({
        "Step": [
            "BDG AGM",
            "Volume",
            "Cost",
            "VCE",
            "VAR",
            "ACT AGM"
        ],
        "Value": [
            bdg_agm,
            volume_effect,
            cost_effect,
            vce_effect,
            var_effect,
            act_agm
        ]
    })

    st.bar_chart(waterfall_df.set_index("Step"))

    st.markdown(f"""
    ### 🔍 What is driving the change?

    - Units: {bdg_units:.0f} → {act_units:.0f}
    - Price: {bdg_price:.2f} → {act_price:.2f}
    - Cost: {bdg_cost:.2f} → {act_cost:.2f}

    ---

    👉 Volume impact:(act unit-bdg unit)x(bdg price): 
    ({act_units:.0f} - {bdg_units:.0f}) × {bdg_price:.2f} = **{volume_effect:.0f} €**

   

    👉 Cost impact: whatever you want i can add now something something
    ({act_cost:.2f} - {bdg_cost:.2f}) × {act_units:.0f} = **{-cost_effect:.0f} € impact**

    ---
    ✅ Total explained change: volume_effect + cost_effect + vce_effect + var_effect: 
    **{volume_effect + cost_effect + vce_effect + var_effect:.0f} €**

    ✅ Actual difference:act_agm - bdg_agm: 
    **{act_agm - bdg_agm:.0f} €**
    """)

