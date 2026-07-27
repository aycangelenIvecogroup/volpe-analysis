import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

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
        "TN": "tn",
        "AGM": "agm"
    })[["customer", "tn", "agm"]]

    act = fix_customer(act)

    act["tn"] = pd.to_numeric(act["tn"], errors="coerce")
    act["agm"] = pd.to_numeric(act["agm"], errors="coerce")

    act = act.fillna(0)

    act = act.groupby("customer", as_index=False)[["tn", "agm"]].sum()

    act["SCENARIO"] = "ACT"


    # === BDG ===
    bdg = pd.read_excel(BASE_PATH / "BDG2026_v4_clean.xlsx")
    bdg = clean_cols(bdg)

    bdg = bdg.rename(columns={
        "CUSTOMER MERGE": "customer",
        "TN": "tn",
        "AGM": "agm"
    })[["customer", "tn", "agm"]]


    bdg = fix_customer(bdg)

    bdg["tn"] = pd.to_numeric(bdg["tn"], errors="coerce")
    bdg["agm"] = pd.to_numeric(bdg["agm"], errors="coerce")

    bdg = bdg.fillna(0)

    bdg = bdg.groupby("customer", as_index=False)[["tn", "agm"]].sum()

    bdg["SCENARIO"] = "BDG"

    # === LY ===
    ly = pd.read_excel(BASE_PATH / "LY25_clean.xlsx")
    ly = clean_cols(ly)

    ly = ly.rename(columns={
        "CUSTOMER MERGE": "customer",
        "TN": "tn",
        "AGM": "agm"
    })[["customer", "tn", "agm"]]

    ly = fix_customer(ly)

    ly["tn"] = pd.to_numeric(ly["tn"], errors="coerce")
    ly["agm"] = pd.to_numeric(ly["agm"], errors="coerce")

    ly = ly.fillna(0)

    ly = ly.groupby("customer", as_index=False)[["tn", "agm"]].sum()

    ly["SCENARIO"] = "LY"

    fcs = pd.read_excel(BASE_PATH / "fcst1_2026_clean.xlsx")
    fcs = clean_cols(fcs)

    fcs = fcs.rename(columns={
        "CUSTOMER MERGE": "customer",
        "TN": "tn",
        "AGM": "agm"
    })[["customer", "tn", "agm"]]


    fcs = fix_customer(fcs)

    fcs["tn"] = pd.to_numeric(fcs["tn"], errors="coerce")
    fcs["agm"] = pd.to_numeric(fcs["agm"], errors="coerce")

    fcs = fcs.fillna(0)

    fcs = fcs.groupby("customer", as_index=False)[["tn", "agm"]].sum()

    fcs["SCENARIO"] = "FCS1"


    # ✅ CONCAT (ARTIK SAFE)
    df = pd.concat([act, bdg, ly, fcs], ignore_index=True)

    return df

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

    df = load_data()  # ✅ EN ÜSTE AL

    # ======================
    # HEADER
    # ======================
    col_title, col_controls = st.columns([4, 2])

    with col_title:
        st.title("📊 Customer Performance")

    with col_controls:

        st.markdown("### ⚙️ Controls")

        # ✅ KPI DETAILS
        selected_scenarios = st.multiselect(
            "📊 Select Scenarios",
            ["ACT", "BDG", "FCS1", "LY"],
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
            index=3  # ✅ Apr default
        )

        months = month_map[selected_month]

        
       


    # ======================
    # FILTERS
    # ======================
    st.markdown("### 🔎 Filters")

    col1, col2 = st.columns([2, 3])

    with col1:
        selected_customers = st.multiselect(
            "Select Customers",
            options=sorted(df["customer"].unique())
        )




    # ======================
    # PIVOT
    # ======================
    pivot = df.pivot(index="customer", columns="SCENARIO", values=["tn", "agm"]).fillna(0)
    pivot.columns = [f"{m}_{s}" for m, s in pivot.columns]
    pivot = pivot.reset_index()

    # ======================
    # APPLY FILTERS ✅
    # ======================

    # Customer seçilmişse
    if selected_customers:
        pivot = pivot[pivot["customer"].isin(selected_customers)]



    # ======================
    # CALC ✅
    # ======================
    pivot["tn_runrate"] = pivot["tn_ACT"] / months * 12
    pivot["agm_runrate"] = pivot["agm_ACT"] / months * 12

    pivot["margin_YTD"] = pivot["agm_ACT"] / pivot["tn_ACT"].replace(0, np.nan)

    pivot["margin_BDG"] = pivot["agm_BDG"] / pivot["tn_BDG"].replace(0, np.nan)
    pivot["margin_LY"] = pivot["agm_LY"] / pivot["tn_LY"].replace(0, np.nan)

    pivot["Δ_BDG_TN"] = (pivot["tn_runrate"] / pivot["tn_BDG"] - 1) * 100
    pivot["Δ_LY_TN"] = (pivot["tn_runrate"] / pivot["tn_LY"] - 1) * 100

    pivot["Δ_BDG_margin"] = (pivot["margin_YTD"] - pivot["margin_BDG"]) * 100
    pivot["Δ_LY_margin"] = (pivot["margin_YTD"] - pivot["margin_LY"]) * 100

    pivot["margin_FCS1"] = pivot["agm_FCS1"] / pivot["tn_FCS1"].replace(0, np.nan)

    pivot["Δ_FCS1_TN"] = (pivot["tn_runrate"] / pivot["tn_FCS1"] - 1) * 100
    pivot["Δ_FCS1_margin"] = (pivot["margin_YTD"] - pivot["margin_FCS1"]) * 100

    pivot = pivot[pivot["tn_ACT"] > 0]
    # ✅ EN BÜYÜK CUSTOMER ÜSTTE
    pivot = pivot.sort_values("tn_ACT", ascending=True)
    threshold = 1_000_000

    pivot.loc[pivot["tn_BDG"] < threshold, "Δ_BDG_TN"] = np.nan
    pivot.loc[pivot["tn_LY"] < threshold, "Δ_LY_TN"] = np.nan
    pivot.loc[pivot["tn_FCS1"] < threshold, "Δ_FCS1_TN"] = np.nan

    # ======================
    # KPI ✅
    # ======================
    st.markdown("## Overview")
    st.caption(f"""
    RunRate is calculated based on performance up to **{selected_month}**
    ({months} months YTD), annualized to full year.
    """)

    c1, c2, c3 = st.columns(3)

    total_tn = pivot["tn_runrate"].sum()
    total_agm = pivot["agm_runrate"].sum()
    total_margin = total_agm / total_tn if total_tn != 0 else np.nan

    c1.metric("TN RunRate", euro(total_tn))
    c2.metric("AGM RunRate", euro(total_agm))
    c3.metric("Margin", pct(total_margin * 100))


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
        })

        # TN
        rows.append({
            "Customer": r["customer"],
            "Type": "TN",
            "Metric": f"TN RunRate ({selected_month} YTD): {euro(r['tn_runrate'])}",
            "ACT (€)": euro(r["tn_runrate"]),
            "Margin (%)": "",
            "Δ BDG": pct(r["Δ_BDG_TN"]),
            "Δ FCS1": pct(r["Δ_FCS1_TN"]),
            "Δ LY": pct(r["Δ_LY_TN"]),
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



    styled = final_df.style.map(highlight, subset=["Δ BDG","Δ FCS1","Δ LY"])
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
                "margin_YTD",
                "tn_runrate",
                "agm_runrate"
            ]].copy()

            # ===== FORMAT =====
            df_act["TN"] = df_act["tn_ACT"].apply(number)
            df_act["AGM (€)"] = df_act["agm_ACT"].apply(euro)
            df_act["Margin (%)"] = df_act["margin_YTD"].apply(lambda x: f"{x*100:.2f}%")

            df_act["RunRate TN"] = df_act["tn_runrate"].apply(euro)
            df_act["RunRate AGM"] = df_act["agm_runrate"].apply(euro)

            st.dataframe(
                df_act[[
                    "customer",
                    "TN",
                    "AGM (€)",
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
                "margin_YTD","margin_BDG"
            ]].copy()

            df_bdg["TN ACT"] = df_bdg["tn_ACT"].apply(number)
            df_bdg["TN BDG"] = df_bdg["tn_BDG"].apply(number)

            df_bdg["AGM ACT (€)"] = df_bdg["agm_ACT"].apply(euro)
            df_bdg["AGM BDG (€)"] = df_bdg["agm_BDG"].apply(euro)

            df_bdg["Margin ACT (%)"] = df_bdg["margin_YTD"].apply(lambda x: f"{x*100:.2f}%")
            df_bdg["Margin BDG (%)"] = df_bdg["margin_BDG"].apply(lambda x: f"{x*100:.2f}%")

            st.dataframe(
                df_bdg[[
                    "customer",
                    "TN ACT","TN BDG",
                    "AGM ACT (€)","AGM BDG (€)",
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
                "margin_YTD","margin_FCS1"
            ]].copy()

            df_fcs["TN ACT"] = df_fcs["tn_ACT"].apply(number)
            df_fcs["TN FCS"] = df_fcs["tn_FCS1"].apply(number)

            df_fcs["AGM ACT (€)"] = df_fcs["agm_ACT"].apply(euro)
            df_fcs["AGM FCS (€)"] = df_fcs["agm_FCS1"].apply(euro)

            df_fcs["Margin ACT (%)"] = df_fcs["margin_YTD"].apply(lambda x: f"{x*100:.2f}%")
            df_fcs["Margin FCS (%)"] = df_fcs["margin_FCS1"].apply(lambda x: f"{x*100:.2f}%")

            st.dataframe(
                df_fcs[[
                    "customer",
                    "TN ACT","TN FCS",
                    "AGM ACT (€)","AGM FCS (€)",
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
                "margin_YTD","margin_LY"
            ]].copy()

            df_ly["TN ACT"] = df_ly["tn_ACT"].apply(number)
            df_ly["TN LY"] = df_ly["tn_LY"].apply(number)

            df_ly["AGM ACT (€)"] = df_ly["agm_ACT"].apply(euro)
            df_ly["AGM LY (€)"] = df_ly["agm_LY"].apply(euro)

            df_ly["Margin ACT (%)"] = df_ly["margin_YTD"].apply(lambda x: f"{x*100:.2f}%")
            df_ly["Margin LY (%)"] = df_ly["margin_LY"].apply(lambda x: f"{x*100:.2f}%")

            st.dataframe(
                df_ly[[
                    "customer",
                    "TN ACT","TN LY",
                    "AGM ACT (€)","AGM LY (€)",
                    "Margin ACT (%)","Margin LY (%)"
                ]],
                use_container_width=True
            )


    # ✅ TEMİZ HEADERS
    def clean_col(c):
        c = c.replace("_", " ")
        c = c.replace("Tn", "TN")
        c = c.replace("Agm", "AGM")
        return c

    final_df.columns = [clean_col(c) for c in final_df.columns]
    # ✅ EURO FORMAT
    for c in [
        "tn ACT","tn BDG","tn FCS1","tn LY",
        "agm ACT","agm BDG","agm FCS1","agm LY"
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

            for c in ["MARGIN YTD","MARGIN BDG","MARGIN FCS1","MARGIN LY"]:
                if c in row:
                    row[c] = ""

        return row

    final_df = final_df.apply(clean_row, axis=1)
    # ✅ ÖNEMLİ KOLONLAR İLK GÖRÜNSÜN
    main_cols = [
        "Customer","Type","Metric",
        "ACT (€)","Margin (%)",
        "Δ BDG","Δ FCS1","Δ LY"
    ]

    other_cols = [c for c in final_df.columns if c not in main_cols]

    final_df = final_df[main_cols + other_cols]



    st.markdown("---")
    st.markdown("## 📊 Insights")

    def prepare_display(df, ref):
        d = df.copy()

        d["TN ACT"] = d["tn_ACT"].apply(euro)
        d[f"TN {ref}"] = d[f"tn_{ref}"].apply(euro)

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
            "Margin Actual", f"Margin {ref}",
            "Δ TN", "Δ Margin",
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

