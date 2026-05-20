import streamlit as st
import pandas as pd
from pathlib import Path
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

BASE_PATH = Path("data/raw")

@st.cache_data(show_spinner=False)
def load_all_data():

    def clean_columns(df):
        df.columns = (
            df.columns.astype(str)
            .str.replace("\n", " ")
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
            .str.upper()
        )
        return df

    # ======================
    # ACT
    # ======================
    act = pd.read_excel(BASE_PATH / "product_raw_db_c03.xlsx", sheet_name="Table1")
    act = clean_columns(act)

    act = act.rename(columns={
        "CUSTOMER MERGE": "customer",
        "ACT TN": "tn",
        "ACT AGM": "agm"
    })

    act["SCENARIO"] = "ACT"

    # ======================
    # BDG
    # ======================
    bdg = pd.read_excel(BASE_PATH / "product_raw_db_bdg26.xlsx", sheet_name="Table2")
    bdg = clean_columns(bdg)

    bdg = bdg.rename(columns={
        "CUSTOMER MERGE": "customer",
        "TN": "tn",
        "AGM": "agm"
    })

    bdg["SCENARIO"] = "BDG"

    # ======================
    # LY 2025
    # ======================
    ly = pd.read_excel(BASE_PATH / "product_raw_db_c12_2025.xlsx", sheet_name="Table1")
    ly = clean_columns(ly)

    ly = ly.rename(columns={
        "CUSTOMER MERGE": "customer",
        "ACT TN": "tn",
        "ACT AGM": "agm"
    })

    ly["SCENARIO"] = "LY"

    # ======================
    # FCS1
    # ======================
    fcs = pd.read_excel(BASE_PATH / "raw_fcs1_26.xlsx")
    fcs = clean_columns(fcs)

    fcs = fcs.rename(columns={
        "CUSTOMER MERGE": "customer",
        "FY TN": "tn",
        "AGM": "agm"
    })

    fcs["SCENARIO"] = "FCS1"

    # ======================
    # CONCAT
    # ======================
    df = pd.concat([act, bdg, ly, fcs], ignore_index=True)

    for c in ["tn", "agm"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    return df

# ==================================================
# PAGE
# ==================================================
def render_dashboard():
    
    def format_euro_short(x):
        if pd.isna(x) or x == "":
            return ""

        try:
            x = float(x)
        except:
            return ""

        if abs(x) >= 1_000_000:
            return f"€ {x/1_000_000:.1f}M"
        elif abs(x) >= 1_000:
            return f"€ {x/1_000:.1f}K"
        else:
            return f"€ {x:.0f}"

     

    st.title("📊 Customer Performance vs Scenarios")

    # months selector (mart = 3)
    months_passed = st.sidebar.slider("Months passed", 1, 12, 3)
    show_scenarios = st.sidebar.checkbox("Show scenario columns", value=False)
    show_details = st.sidebar.checkbox("Show detailed values", value=False)

    st.markdown(f"""
    ### 📘 Simple explanation
    We compare:
    - TN → RunRate vs Budget (%)
    - Margin → YTD vs Budget (pp)
    """)


    df = load_all_data()
  
    # ======================
    # AGGREGATION
    # ======================
    agg = df.groupby(["customer", "SCENARIO"]).agg({
        "tn": "sum",
        "agm": "sum"
    }).reset_index()

    # pivot
    pivot = agg.pivot(index="customer", columns="SCENARIO", values=["tn", "agm"]).fillna(0)

    # flatten columns
    pivot.columns = [f"{m}_{s}" for m, s in pivot.columns]
    
    pivot["tn_runrate"] = pivot["tn_ACT"] / months_passed * 12
    pivot["agm_runrate"] = pivot["agm_ACT"] / months_passed * 12

    pivot["margin_YTD"] = pivot["agm_runrate"] / pivot["tn_runrate"].replace(0, np.nan)

    # ======================
    # CALCULATIONS
    # ======================

    # ======================
    # MARGINS (FULL YEAR SCENARIOS)
    # ======================
    pivot["margin_BDG"] = pivot["agm_BDG"] / pivot["tn_BDG"].replace(0, np.nan)
    pivot["margin_FCS1"] = pivot["agm_FCS1"] / pivot["tn_FCS1"].replace(0, np.nan)
    pivot["margin_LY"] = pivot["agm_LY"] / pivot["tn_LY"].replace(0, np.nan)

    # ======================
    # DELTAS (USING RUN RATE)
    # ======================

    # margin deltas (pp)
    pivot["Δ_BDG_margin"] = pivot["margin_YTD"] - pivot["margin_BDG"]
    pivot["Δ_FCS1_margin"] = pivot["margin_YTD"] - pivot["margin_FCS1"]
    pivot["Δ_LY_margin"] = pivot["margin_YTD"] - pivot["margin_LY"]

    # TN deltas (growth vs full year)
    pivot["Δ_BDG_TN"] = pivot["tn_runrate"] / pivot["tn_BDG"].replace(0, np.nan) - 1
    pivot["Δ_FCS1_TN"] = pivot["tn_runrate"] / pivot["tn_FCS1"].replace(0, np.nan) - 1
    pivot["Δ_LY_TN"] = pivot["tn_runrate"] / pivot["tn_LY"].replace(0, np.nan) - 1

    pivot["Δ_BDG_AGM"] = pivot["agm_runrate"] / pivot["agm_BDG"].replace(0, np.nan) - 1
    pivot["Δ_FCS1_AGM"] = pivot["agm_runrate"] / pivot["agm_FCS1"].replace(0, np.nan) - 1
    pivot["Δ_LY_AGM"] = pivot["agm_runrate"] / pivot["agm_LY"].replace(0, np.nan) - 1
    
    # ======================
    # SEGMENTATION ✅
    # ======================
    def classify(row):
        if row["Δ_BDG_TN"] > 0.1 and row["Δ_BDG_margin"] > 0.005:
            return "⭐ Star"
        elif row["Δ_BDG_TN"] < 0 and row["Δ_BDG_margin"] < 0:
            return "🔴 At Risk"
        else:
            return "🟡 Mixed"

    pivot = pivot.reset_index()

    pivot["Segment"] = pivot.apply(classify, axis=1)

    pivot = pivot.reset_index()
    # ======================
    # KPI BLOCK ✅
    # ======================
    st.markdown("## 📈 Overall KPIs")
    
    total_tn = pivot["tn_ACT"].sum()
    total_runrate = pivot["tn_runrate"].sum()
    avg_margin = pivot["margin_YTD"].mean() * 100
    bdg_gap = (total_runrate / pivot["tn_BDG"].sum() - 1) * 100

    col1, col2, col3, col4 = st.columns(4)

    
    col1.metric("TN (YTD)", format_euro_short(total_tn))
    col2.metric("Run Rate", format_euro_short(total_runrate))

    col3.metric("Avg YTD Margin", f"{avg_margin:.1f}%")
    col4.metric("vs BDG", f"{bdg_gap:.1f}%", delta=f"{bdg_gap:.1f}%")

    # ✅ YENI KPI'LAR (OPSİYONEL)
    if show_scenarios:
        st.markdown("### 📊 Scenario Margins")

        c1, c2, c3 = st.columns(3)

        c1.metric("BDG Margin", f"{(pivot['margin_BDG'].mean()*100):.1f}%")
        c2.metric("FCS1 Margin", f"{(pivot['margin_FCS1'].mean()*100):.1f}%")
        c3.metric("LY Margin", f"{(pivot['margin_LY'].mean()*100):.1f}%")
        
    pivot = pivot[pivot["tn_ACT"] != 0]

    # ======================
    # BUILD FINAL TABLE
    # ======================
    rows = []

    for _, r in pivot.iterrows():

        customer = r["customer"]
        
        # AGM row (with BDG + FCS insight)

        margin = r["margin_YTD"] * 100 if pd.notna(r["margin_YTD"]) else 0
        delta_bdg = r["Δ_BDG_margin"] * 100
        delta_fcs = r["Δ_FCS1_margin"] * 100

        delta_agm_bdg = r["Δ_BDG_AGM"] * 100
        delta_agm_fcs = r["Δ_FCS1_AGM"] * 100

        sign_bdg = "+" if delta_bdg > 0 else ""
        sign_fcs = "+" if delta_fcs > 0 else ""

        tn = r["tn_ACT"]
        

        if show_details:
            metric_text = (
                f"YTD Margin: {margin:.1f}% | "
                f"AGM RunRate: {format_euro_short(r['agm_runrate'])} | "
                f"TN: {format_euro_short(tn)} | "
                f"RunRate: {format_euro_short(r['tn_runrate'])} "
                f"(Δ BDG: {sign_bdg}{delta_bdg:.1f} pp | Δ FCS: {sign_fcs}{delta_fcs:.1f} pp)"
            )
        else:
            metric_text = (
                f"AGM YTD: {format_euro_short(r['agm_ACT'])} | RunRate: {format_euro_short(r['agm_runrate'])} "
                f"(vs BDG: {delta_agm_bdg:.1f}% | vs FCS: {delta_agm_fcs:.1f}%) | "
                f"YTD Margin: {margin:.1f}% "
                f"(Δ BDG: {sign_bdg}{delta_bdg:.1f} pp | Δ FCS: {sign_fcs}{delta_fcs:.1f} pp)"
                            )
       
        rows.append({
            "Customer": customer,
            "Type": "AGM",
            "Metric": metric_text,
            "ACT": r["agm_ACT"],
            "ACT %": margin,
            "Δ FCS1": delta_fcs,
            "Δ BDG26": delta_bdg,
            "Δ LY2025": r["Δ_LY_margin"] * 100,
        })

        


        # TN row (with BDG + FCS insight)

        tn = r["tn_ACT"]
        delta_bdg = r["Δ_BDG_TN"] * 100
        delta_fcs = r["Δ_FCS1_TN"] * 100
        delta_agm_bdg = r["Δ_BDG_AGM"] * 100
        delta_agm_fcs = r["Δ_FCS1_AGM"] * 100

        sign_bdg = "+" if delta_bdg > 0 else ""
        sign_fcs = "+" if delta_fcs > 0 else ""
        if show_details:
            metric_text = (
                f"TN: €{tn:,.0f} | RunRate: €{r['tn_runrate']:,.0f} "
                f"(vs BDG: {sign_bdg}{delta_bdg:.1f}% | vs FCS: {sign_fcs}{delta_fcs:.1f}%)"
                )
        else:
            metric_text = (
                f"TN YTD: {format_euro_short(tn)} | RunRate: {format_euro_short(r['tn_runrate'])} "
                f"(vs BDG: {sign_bdg}{delta_bdg:.1f}% | vs FCS: {sign_fcs}{delta_fcs:.1f}%)"
                )    
        rows.append({
            "Customer": customer,
            "Type": "TN",
            "Metric": metric_text,
            "ACT": tn,
            "ACT %": None,
            "Δ FCS1": delta_fcs,
            "Δ BDG26": delta_bdg,
            "Δ LY2025": r["Δ_LY_TN"] * 100,
        })

    final_df = pd.DataFrame(rows)
    if show_scenarios:
        scenario_cols = pivot[[
            "customer",
            "agm_BDG", "agm_FCS1", "agm_LY",
            "tn_BDG", "tn_FCS1", "tn_LY",
            "margin_BDG", "margin_FCS1", "margin_LY"
        ]].copy()

        # margin to %
        for c in ["margin_BDG", "margin_FCS1", "margin_LY"]:
            scenario_cols[c] *= 100

        final_df = final_df.merge(
            scenario_cols,
            left_on="Customer",
            right_on="customer",
            how="left"
        ).drop(columns=["customer"])

        # ✅ ROW BASED CLEANING
        def clean_scenarios(row):
            row = row.copy()

            if row["Type"] == "AGM":
                # TN kolonlarını boş yap
                row["tn_BDG"] = np.nan
                row["tn_FCS1"] = np.nan
                row["tn_LY"] = np.nan

            elif row["Type"] == "TN":
                # AGM kolonlarını boş yap
                row["agm_BDG"] = np.nan
                row["agm_FCS1"] = np.nan
                row["agm_LY"] = np.nan

                row["margin_BDG"] = np.nan
                row["margin_FCS1"] = np.nan
                row["margin_LY"] = np.nan

            return row

        final_df = final_df.apply(clean_scenarios, axis=1)


    
    def format_pct(x):
        if pd.isna(x) or x == "":
            return ""
        return f"{x:.1f}%"

    def format_pp(x):
        if pd.isna(x) or x == "":
            return ""
        return f"{x:.1f} pp"

    soft_cmap = LinearSegmentedColormap.from_list(
        "soft_red_green",
        ["#f7b3e6", "#fff3cd", "#c6f7d0"]  # soft pink → yellow → green
    )

    def smart_format(val, metric):
        if pd.isna(val):
            return ""

        # AGM row → pp
        if "Margin:" in metric:
            return f"{val:.1f} pp"

        # TN row → %
        if "TN:" in metric:
            return f"{val:.1f}%"

        return val

    # ======================
    # ROW-LEVEL FORMATTING ✅
    # ======================

    def smart_format_row(row):
        res = row.copy()

        is_margin = "Margin" in row["Metric"]

        for col in ["Δ FCS1", "Δ BDG26", "Δ LY2025"]:
            val = row[col]

            if pd.isna(val):
                res[col] = ""
            elif is_margin:
                res[col] = f"{val:.1f} pp"
            else:
                res[col] = f"{val:.1f}%"

        return res

    final_df = final_df.apply(smart_format_row, axis=1)
    # ✅ Kolon isimlerini netleştir
    final_df = final_df.rename(columns={
        "ACT": "ACT (€)",
        "ACT %": "Margin (%)"
    })

    format_dict = {
        "ACT (€)": format_euro_short,
        "Margin (%)": format_pct,
    }


    # ✅ scenario kolonları varsa onları da formatla
    if show_scenarios:
        format_dict.update({
            "tn_BDG": format_euro_short,
            "tn_FCS1": format_euro_short,
            "tn_LY": format_euro_short,
            
            "agm_BDG": format_euro_short,
            "agm_FCS1": format_euro_short,
            "agm_LY": format_euro_short,

            
            "margin_BDG": format_pct,
            "margin_FCS1": format_pct,
            "margin_LY": format_pct,

        })

    styled = final_df.style.format(format_dict)
    def color_scale(val):
        try:
            raw = float(str(val).replace("%", "").replace("pp", ""))
        except:
            return ""

        # ✅ AYNI SCALE KALSIN AMA ANLAMLI
        if raw > 2:
            return "background-color: #c6f7d0"
        elif raw < -2:
            return "background-color: #f7c6c7"
        else:
            return "background-color: #fff3cd"


    styled = styled.map(color_scale, subset=[
        "Δ FCS1", "Δ BDG26", "Δ LY2025"
    ])
    with st.expander("ℹ️ How is RunRate calculated?"):
        st.write(f"""
    RunRate = (YTD / months) × 12

    Example:
    €300K after {months_passed} months  
    → 300 / {months_passed} × 12 = €1.2M

    YTD = actual  
    RunRate = full year estimate
    """)

    # ======================
    # OUTPUT
    # ======================
    st.dataframe(styled, use_container_width=True)
    st.markdown("""
    ### 🧩 Segmentation Logic

    Customers are classified based on performance vs **Budget (BDG)**:
    - ⭐ **Star**
    - TN > BDG (Δ TN > 0)
    - Margin > BDG (Δ Margin > 0)
    - 🔴 **At Risk**
    - TN < BDG (Δ TN < 0)
    - Margin < BDG (Δ Margin < 0)
    - 🟡 **Mixed**: One metric positive, one negative
    ---
    ### 📏 Thresholds
    - Δ TN = `(RunRate / BDG) - 1`
    - Δ Margin = `RunRate margin - BDG margin`
    """)
    # ==================================================
    # 🔍 INSIGHT ANALYSIS
    # ==================================================
    st.markdown("## 🧠 Customer Segmentation")

    st.dataframe(
        pivot[["customer", "Segment", "Δ_BDG_TN", "Δ_BDG_margin"]],
        use_container_width=True
    )
    st.markdown("## 🔍 Customer Insights")

    insight_df = pivot.copy()

    # --------------------------------------
    # Helper functions 
    # --------------------------------------
    def build_table(df, col, title_best, title_worst):

        df = df.copy()
        df["abs"] = df[col].abs()

        closest = df.nsmallest(5, "abs")
        worst = df.nlargest(5, "abs")

        def explain(row, metric):
            value = row[col] * 100

            if metric == "margin":
                if value > 0:
                    return f"Margin higher than target (+{value:.1f}pp)"
                else:
                    return f"Margin below target ({value:.1f}pp)"

            else:
                if value > 0:
                    return f"TN above target (+{value:.1f}%)"
                else:
                    return f"TN below target ({value:.1f}%)"

        closest["Insight"] = closest.apply(lambda r: explain(r, "margin"), axis=1)
        worst["Insight"] = worst.apply(lambda r: explain(r, "margin"), axis=1)

        return closest[["customer", col, "Insight"]], worst[["customer", col, "Insight"]]

    # ======================================
    # ✅ BDG ANALYSIS
    # ======================================
    st.markdown("### 📊 Vs Budget (BDG26)")

    best_bdg, worst_bdg = build_table(insight_df, "Δ_BDG_margin", "Closest", "Worst")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### ✅ Closest to Budget")
        st.dataframe(best_bdg.rename(columns={
            "customer": "Customer",
            "Δ_BDG_margin": "Δ Margin"
        }), use_container_width=True)

    with col2:
        st.markdown("#### 🔴 Furthest from Budget")
        st.dataframe(worst_bdg.rename(columns={
            "customer": "Customer",
            "Δ_BDG_margin": "Δ Margin"
        }), use_container_width=True)

    # ======================================
    # ✅ FCS ANALYSIS
    # ======================================
    st.markdown("### 🔮 Vs Forecast (FCS1)")

    best_fcs, worst_fcs = build_table(insight_df, "Δ_FCS1_margin", "Closest", "Worst")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### ✅ Closest to Forecast")
        st.dataframe(best_fcs.rename(columns={
            "customer": "Customer",
            "Δ_FCS1_margin": "Δ Margin"
        }), use_container_width=True)

    with col2:
        st.markdown("#### 🔴 Furthest from Forecast")
        st.dataframe(worst_fcs.rename(columns={
            "customer": "Customer",
            "Δ_FCS1_margin": "Δ Margin"
        }), use_container_width=True)

    # ======================================
    # ✅ LY ANALYSIS
    # ======================================
    st.markdown("### 📈 Vs Last Year (LY2025)")

    # burada direction önemli → best = highest
    best_ly = insight_df.nlargest(5, "Δ_LY_margin")
    worst_ly = insight_df.nsmallest(5, "Δ_LY_margin")

    def explain_ly(row):
        value = row["Δ_LY_margin"] * 100
        if value > 0:
            return f"Margin improved vs LY (+{value:.1f}pp)"
        else:
            return f"Margin declined vs LY ({value:.1f}pp)"

    best_ly["Insight"] = best_ly.apply(explain_ly, axis=1)
    worst_ly["Insight"] = worst_ly.apply(explain_ly, axis=1)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🟢 Best vs Last Year")
        st.dataframe(best_ly[["customer", "Δ_LY_margin", "Insight"]].rename(columns={
            "customer": "Customer",
            "Δ_LY_margin": "Δ Margin"
        }), use_container_width=True)

    with col2:
        st.markdown("#### 🔴 Worst vs Last Year")
        st.dataframe(worst_ly[["customer", "Δ_LY_margin", "Insight"]].rename(columns={
            "customer": "Customer",
            "Δ_LY_margin": "Δ Margin"
        }), use_container_width=True)
    # ======================
    # ALERTS ✅
    # ======================
    st.markdown("""
    ### ⚙️ How numbers are calculated

    - TN:
    → RunRate vs target → gives %

    - Margin:
    → YTD margin vs target → gives pp

    Example:

    TN:
    1.2M vs 1.0M → +20%

    Margin:
    12% vs 10% → +2pp
    """)

    st.markdown("## 🚨 Risky Customers")

    alerts = pivot[
        (pivot["Δ_BDG_margin"] < -0.05) | 
        (pivot["Δ_BDG_TN"] < -0.1)
    ]
    
    alerts_display = alerts.copy()

    alerts_display["Δ_BDG_margin"] = alerts_display["Δ_BDG_margin"] * 100
    alerts_display["Δ_BDG_TN"] = alerts_display["Δ_BDG_TN"] * 100

    alerts_display["Δ_BDG_margin"] = alerts_display["Δ_BDG_margin"].apply(lambda x: f"{x:.1f} pp")
    alerts_display["Δ_BDG_TN"] = alerts_display["Δ_BDG_TN"].apply(lambda x: f"{x:.1f}%")
    
    def alert_explain(row):
        margin = float(row["Δ_BDG_margin"].replace(" pp", ""))
        tn = float(row["Δ_BDG_TN"].replace("%", ""))

        if margin < 0 and tn < 0:
            return "Revenue & margin below target"
        elif margin < 0:
            return "Margin dilution"
        elif tn < 0:
            return "Volume underperformance"
        else:
            return "OK"

    alerts_display["Insight"] = alerts_display.apply(alert_explain, axis=1)

    st.dataframe(
        alerts_display[["customer", "Δ_BDG_margin", "Δ_BDG_TN", "Insight"]],
        use_container_width=True
    )
