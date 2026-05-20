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

    # ✅ BURADA hesapla (string dışında!)
    delta_strategy = (bdg['margin'] - fy['margin']) * 100
    delta_execution = (act['margin'] - bdg['margin']) * 100

    explanation = f"""
### 📌 STRATEGY VS EXECUTION

- Strategy (AGM): **{strategy_gap:,.0f} €**
- Execution (AGM): **{execution_gap:,.0f} €**

---

# 🔬 FULL PERFORMANCE ANALYSIS

## 🟦 1. STRATEGY (FY25 → BDG)

**Margin:**
- {fy['margin']*100:.1f}% → {bdg['margin']*100:.1f}%
- Δ **{delta_strategy:+.1f} pp**

**TN:**
- {fy['tn']:,.0f} € → {bdg['tn']:,.0f} €
- Δ **{bdg['tn'] - fy['tn']:+,.0f} €**

**COGS:**
- {fy['cogs']:,.0f} € → {bdg['cogs']:,.0f} €
- Δ **{bdg['cogs'] - fy['cogs']:+,.0f} €**

---

## 🟥 2. EXECUTION (BDG → ACT)

**Margin:**
- {bdg['margin']*100:.1f}% → {act['margin']*100:.1f}%
- Δ **{delta_execution:+.1f} pp**

**TN:**
- {bdg['tn']:,.0f} € → {act['tn']:,.0f} €
- Δ **{act['tn'] - bdg['tn']:+,.0f} €**

**COGS:**
- {bdg['cogs']:,.0f} € → {act['cogs']:,.0f} €
- Δ **{act['cogs'] - bdg['cogs']:+,.0f} €**

---

## 🟨 3. UNIT ECONOMICS

**Unit Price:**
- ACT: **{act['unit_price']:,.2f} €/unit**  
  ({act['tn']:,.0f} € / {act['units']:,.0f})

- BDG: **{bdg['unit_price']:,.2f} €/unit**  
  ({bdg['tn']:,.0f} € / {bdg['units']:,.0f})

**Unit Cost:**
- ACT: **{act['unit_cost']:,.2f} €/unit**  
  ({act['cogs']:,.0f} € / {act['units']:,.0f})

- BDG: **{bdg['unit_cost']:,.2f} €/unit**  
  ({bdg['cogs']:,.0f} € / {bdg['units']:,.0f})

---

## 🟥 ROOT CAUSE
"""


    # ROOT CAUSE TAGS
    if act["unit_cost"] > bdg["unit_cost"]:
        explanation += "- 🔺 Cost inflation (unit cost increased)\n"
    if act["unit_price"] < bdg["unit_price"]:
        explanation += "- 🔻 Pricing pressure (unit price decreased)\n"
    if act["units"] >= bdg["units"]:
        explanation += "- 📦 Volume is not the main issue\n"


    explanation += """

---

## ✅ CONCLUSION

Variance is mainly driven by **cost vs pricing imbalance**,  
validated at unit level.

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
    
    st.dataframe(
        df_group.style.format({
            "units": "{:,.0f}",
            "tn": "{:,.0f} €",
            "cogs": "{:,.0f} €",
            "agm": "{:,.0f} €",
            "vce": "{:,.0f} €",
            "sgm": "{:,.0f} €",
        }),
        use_container_width=True
    )


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
    
    st.dataframe(
        comp.style.format({
            "FY25": "{:,.0f} €",
            "BDG": "{:,.0f} €",
            "ACT": "{:,.0f} €",
            "Strategy (BDG-FY25)": "{:,.0f} €",
            "Execution (ACT-BDG)": "{:,.0f} €",
        }),
        use_container_width=True
    )


    # =========================
    # EXPLANATION
    # =========================
    metrics = compute_metrics(df_group)
    explanation = build_explanation(metrics)
    total_gap = df_group.loc["MARCH", "agm"] - df_group.loc["BDG", "agm"]

    if total_gap < 0:
        trend = "🔴 DECLINING"
    else:
        trend = "🟢 IMPROVING"

    st.markdown(f"""
    ## 📊 OVERALL RESULT

    ### {trend}

    ### Impact: **{total_gap:+,.0f} €**
    """)
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
    product_table["Δ AGM (€)"] = product_table["ACT AGM"] - product_table["BDG AGM"]
    product_table["Δ SGM (€)"] = product_table["ACT SGM"] - product_table["BDG SGM"]

    product_table["Δ AGM % pp"] = (product_table["ACT AGM %"] - product_table["BDG AGM %"])*100
    product_table["Δ SGM % pp"] = (product_table["ACT SGM %"] - product_table["BDG SGM %"])*100

    # ====================================
    # UNIT BASED DRIVER COLUMNS ✅
    # ====================================

    # unit price
    product_table["ACT Unit Price"] = product_table["ACT TN"] / product_table["ACT Units"].replace(0, 1)
    product_table["BDG Unit Price"] = product_table["BDG TN"] / product_table["BDG Units"].replace(0, 1)

    # unit cost
    product_table["ACT Unit Cost"] = product_table["ACT COGS"] / product_table["ACT Units"].replace(0, 1)
    product_table["BDG Unit Cost"] = product_table["BDG COGS"] / product_table["BDG Units"].replace(0, 1)

    # deltas
    product_table["Δ Price"] = product_table["ACT Unit Price"] - product_table["BDG Unit Price"]
    product_table["Δ Cost"] = product_table["ACT Unit Cost"] - product_table["BDG Unit Cost"]

    # margin pressure (MOST IMPORTANT 🔥)
    product_table["Margin Pressure"] = product_table["Δ Price"] - product_table["Δ Cost"]

    product_table = product_table.sort_values("Δ AGM % pp", ascending=True)
    def highlight_all(val, col):

        if col in ["Δ AGM (€)", "Δ SGM (€)", "Margin Pressure"]:
            if val < 0:
                return "color:red"
            elif val > 0:
                return "color:green"

        if col in ["Δ AGM % pp", "Δ SGM % pp"]:
            if val < 0:
                return "color:red"
            elif val > 0:
                return "color:green"

        return ""


    styled_table = product_table.style.format({

        "ACT Units": "{:,.0f}",
        "BDG Units": "{:,.0f}",

        "ACT TN": "{:,.0f} €",
        "BDG TN": "{:,.0f} €",
        "ACT COGS": "{:,.0f} €",
        "BDG COGS": "{:,.0f} €",
        "ACT AGM": "{:,.0f} €",
        "BDG AGM": "{:,.0f} €",
        "ACT SGM": "{:,.0f} €",
        "BDG SGM": "{:,.0f} €",

        "Δ AGM (€)": "{:+,.0f} €",
        "Δ SGM (€)": "{:+,.0f} €",

        
        "Δ AGM % pp": "{:+.1f} pp",
        "Δ SGM % pp": "{:+.1f} pp",


        "Δ Price": "{:+,.2f}",
        "Δ Cost": "{:+,.2f}",
        "Margin Pressure": "{:+,.2f}",

        "ACT Unit Price": "{:,.2f}",
        "BDG Unit Price": "{:,.2f}",
        "ACT Unit Cost": "{:,.2f}",
        "BDG Unit Cost": "{:,.2f}",

    }).apply(
        lambda row: [highlight_all(row[col], col) for col in row.index],
        axis=1
    )
    

    def highlight_problem(val):
        if val < 0:
            return "background-color: #fee2e2"   # kırmızı
        elif val > 0:
            return "background-color: #dcfce7"   # yeşil
        return ""
    
    

    st.dataframe(styled_table, use_container_width=True)
    
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

    def color_delta(val, metric):

        # COGS ters renk
        if metric == "Unit COGS":
            if val > 0:
                return "color: red"
            elif val < 0:
                return "color: green"
            
        if metric == "Unit Variance":
            if val > 0:
                return "color: red"
            elif val < 0:
                return "color: green"

        # diğerleri normal
        if val > 0:
            return "color: green"
        elif val < 0:
            return "color: red"

        return ""
        
    

    def highlight_row(row):
        styles = []

        for col in row.index:
            if col == "Δ":
                styles.append(color_delta(row[col], row["Metric"]))
            else:
                styles.append("")

        return styles


    styled = unit_result.style.apply(highlight_row, axis=1)


    st.dataframe(
        styled.format({
            
            "ACT": "{:,.2f}",
            "BDG": "{:,.2f}",
            "Δ": "{:+,.2f}",

        }),
        use_container_width=True
    )


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
    
    

