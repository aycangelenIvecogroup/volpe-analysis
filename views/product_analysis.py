from pandas import col
import streamlit as st
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

# ==================================================
# LOAD DATA
# ==================================================
BASE_PATH = Path("data/raw")

@st.cache_data
def load_data():

    def load_file(path, scenario):
        if "bdg" in path.name.lower():
            df = pd.read_excel(path, sheet_name="Table2")
        else:
            df = pd.read_excel(path, sheet_name="Table1")

        # CLEAN
        df.columns = (
            df.columns.astype(str)
            .str.replace("\n", " ")
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
            .str.upper()
        )

        # PN
        if "PN ALLESTIMENTO" in df.columns:
            df["pn"] = df["PN ALLESTIMENTO"]
        elif "PN" in df.columns:
            df["pn"] = df["PN"]
        else:
            st.error("PN column not found!")
            st.stop()

        # ✅ EKLENDİ (VCE + COGS)
        df = df.rename(columns={
            "CUSTOMER MERGE": "customer",
            "FAMILY": "family",
            "PRODUCT": "product",
            "POWERNODE": "powernode",
            "ACT UNITS": "units",
            "UNITS": "units",
            "ACT TN": "tn",
            "TN": "tn",
            "ACT AGM": "agm",
            "AGM": "agm",
            "ACT VCE": "vce",
            "VCE": "vce",
            "COGS": "cogs"
        })
        
        
            
        cogs_cols = [col for col in df.columns if "COGS" in col]

        if len(cogs_cols) > 0:
            df["cogs"] = df[cogs_cols[0]]

            
        vce_cols = [col for col in df.columns if "VCE" in col]

        if len(vce_cols) > 0:
            df["vce"] = df[vce_cols[0]]


        # ✅ numeric genişletildi
        for c in ["units", "tn", "agm", "vce", "cogs"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

        df["pn"] = df["pn"].astype(str).str.strip()
        df["SCENARIO"] = scenario

        return df

    c03 = load_file(BASE_PATH / "product_raw_db_c03.xlsx", "ACT")
    bdg = load_file(BASE_PATH / "product_raw_db_bdg26.xlsx", "BDG")
    c12 = load_file(BASE_PATH / "product_raw_db_c12_2025.xlsx", "LY")

    return pd.concat([c03, bdg, c12], ignore_index=True)


# ==================================================
# PAGE
# ==================================================
def render_product_analysis():

    df = load_data()
    def format_euro(x):
        if pd.isna(x):
            return ""
        if abs(x) >= 1_000_000:
            return f"€ {x/1_000_000:.1f}M"
        elif abs(x) >= 1_000:
            return f"€ {x/1_000:.1f}K"
        else:
            return f"€ {x:.0f}"
    st.title("🚀 Product Performance Explorer")

    # ======================
    # SCENARIO SELECTION
    # ======================
    col1, col2 = st.columns(2)

    with col1:
        scen_1 = st.selectbox("Scenario", sorted(df["SCENARIO"].unique()))

    with col2:
        scen_2 = st.selectbox(
            "Compare with",
            ["None"] + sorted(df["SCENARIO"].unique())
        )

    df_1 = df[df["SCENARIO"] == scen_1]
    df_2 = df[df["SCENARIO"] == scen_2] if scen_2 != "None" else None

    # ======================
    # FILTERS
    # ======================
    col3, col4, col5 = st.columns(3)

    with col3:
        selected_family = st.selectbox(
            "Family",
            ["ALL"] + sorted(df["family"].dropna().unique())
        )

    with col4:
        selected_product = st.selectbox(
            "Product",
            ["ALL"] + sorted(df["product"].dropna().unique())
        )
    
    with col5:
        selected_customer = st.multiselect(
            "Customer",
            sorted(df["customer"].dropna().unique())
        )

    
    if selected_customer:
        df_1 = df_1[df_1["customer"].isin(selected_customer)]
        if df_2 is not None:
            df_2 = df_2[df_2["customer"].isin(selected_customer)]

    if selected_family != "ALL":
        df_1 = df_1[df_1["family"] == selected_family]
        if df_2 is not None:
            df_2 = df_2[df_2["family"] == selected_family]

    if selected_product != "ALL":
        df_1 = df_1[df_1["product"] == selected_product]
        if df_2 is not None:
            df_2 = df_2[df_2["product"] == selected_product]

    # ======================
    # AGGREGATION
    # ======================
    pn_1 = df_1.groupby(["pn", "customer"]).agg({
        "family": lambda x: x.mode()[0] if len(x.mode()) > 0 else "",
        "product": lambda x: x.mode()[0] if len(x.mode()) > 0 else "",
        "units": "sum",
        "tn": "sum",
        "agm": "sum",
        "vce": "sum",
        "cogs": "sum"
    }).reset_index()
    customer_count = df_1.groupby("pn")["customer"].nunique()
    pn_1["Customer Count"] = pn_1["pn"].map(customer_count)


    pn_1 = pn_1.reset_index(drop=True)
    
    
    



    # ==================================================
    # ✅ UNIT ENGINE (EN ÖNEMLİ EK)
    # ==================================================
    pn_1["unit_tn"] = pn_1["tn"] / pn_1["units"].replace(0, 1)
    pn_1["unit_agm"] = pn_1["agm"] / pn_1["units"].replace(0, 1)
    pn_1["unit_vce"] = pn_1["vce"] / pn_1["units"].replace(0, 1)
    pn_1["unit_cogs"] = pn_1["cogs"] / pn_1["units"].replace(0, 1)

    # ✅ VAR (residual)
    pn_1["unit_var"] = (
        pn_1["unit_tn"]
        - pn_1["unit_cogs"]
        - pn_1["unit_vce"]
        - pn_1["unit_agm"]
    )
    # ✅ TOTAL VAR (EKLE)
    pn_1["var"] = (
        pn_1["tn"]
        - pn_1["cogs"]
        - pn_1["vce"]
        - pn_1["agm"]
    )


    # ✅ margin artık açık
    
    pn_1["margin (AGM%)"] = (
        pn_1["agm"] / pn_1["tn"].replace(0, 1)
    ) * 100



    # ======================
    # KPI ROW
    # ======================
    colk1, colk2, colk3 = st.columns(3)

    
    colk1.metric("💰 TN (Turnover)", format_euro(pn_1["tn"].sum()))
    colk2.metric("💰 AGM", format_euro(pn_1["agm"].sum()))

    colk3.metric("📊 margin (AGM%)", f"{pn_1['margin (AGM%)'].mean():.1f}%")

    # ======================
    # INSIGHT
    # ======================
    if len(pn_1) > 0:
        top = pn_1["tn"].idxmax()
        worst = pn_1["margin (AGM%)"].idxmin()

        st.info(f"""
        🧠 INSIGHT

        - TN highest product: {top}
        - Lowest margin (AGM%): {worst}

        👉 If margin decreases:
        - Unit TN might be too low (pricing issue)
        - Or COGS / VCE might be too high (cost issue)


        """)

    # BDG / Compare data (unit hesapla)
    if df_2 is not None:
        
        pn_2 = df_2.groupby("pn")[["tn", "agm", "cogs", "vce"]].sum()

        


        pn_2_detail = df_2.groupby("pn").agg({
            "units": "sum",
            "tn": "sum",
            "agm": "sum",
            "vce": "sum",
            "cogs": "sum"
        })

        # unit hesapla
        pn_2_detail["unit_tn"] = pn_2_detail["tn"] / pn_2_detail["units"].replace(0, 1)
        pn_2_detail["unit_agm"] = pn_2_detail["agm"] / pn_2_detail["units"].replace(0, 1)
        pn_2_detail["unit_vce"] = pn_2_detail["vce"] / pn_2_detail["units"].replace(0, 1)
        pn_2_detail["unit_cogs"] = pn_2_detail["cogs"] / pn_2_detail["units"].replace(0, 1)
        
        pn_2_detail["unit_var"] = (
            pn_2_detail["unit_tn"]
            - pn_2_detail["unit_cogs"]
            - pn_2_detail["unit_vce"]
            - pn_2_detail["unit_agm"]
        )



        pn_compare = pn_1.merge(
            pn_2.reset_index(),
            on="pn",
            how="left",
            suffixes=("", "_prev")
        ).fillna(0)

        
        pn_compare["Δ TN"] = pn_compare["tn"] - pn_compare["tn_prev"]
        pn_compare["Δ COGS"] = pn_compare["cogs"] - pn_compare["cogs_prev"]
        pn_compare["Δ VCE"] = pn_compare["vce"] - pn_compare["vce_prev"]
        pn_compare["Δ AGM"] = pn_compare["agm"] - pn_compare["agm_prev"]
        # ✅ VAR (ACT + BDG + DELTA)
        pn_compare["var"] = (
            pn_compare["tn"]
            - pn_compare["cogs"]
            - pn_compare["vce"]
            - pn_compare["agm"]
        )

        pn_compare["var_prev"] = (
            pn_compare["tn_prev"]
            - pn_compare["cogs_prev"]
            - pn_compare["vce_prev"]
            - pn_compare["agm_prev"]
        )

        pn_compare["Δ VAR"] = pn_compare["var"] - pn_compare["var_prev"]


        pn_compare["margin_prev (AGM%)"] = (
            pn_compare["agm_prev"] / pn_compare["tn_prev"].replace(0, 1)
        ) * 100

        pn_compare["Δ margin (AGM%)"] = (
            pn_compare["margin (AGM%)"] - pn_compare["margin_prev (AGM%)"]
        )

        data_for_plot = pn_compare

        st.subheader("📊 Comparison Table")

    else:
        pn_1 = pn_1.sort_values("tn", ascending=False)
        data_for_plot = pn_1
        st.subheader("📊 Product Overview")

    # ✅ format dictionary (temiz versiyon)
    fmt = {
        
        f"TN ({scen_1})": format_euro,
        f"TN ({scen_2})": format_euro,
        f"COGS ({scen_1})": format_euro,
        f"COGS ({scen_2})": format_euro,
        f"VCE ({scen_1})": format_euro,
        f"VCE ({scen_2})": format_euro,
        f"AGM ({scen_1})": format_euro,
        f"AGM ({scen_2})": format_euro,
        f"VAR ({scen_1})": format_euro,
        f"VAR ({scen_2})": format_euro,

        "margin (AGM%)": "{:.1f}%",

        "unit_tn": format_euro,
        "unit_agm": format_euro,
        "unit_cogs": format_euro,
        "unit_vce": format_euro,
        "unit_var": format_euro,
    }


    # ✅ sadece varsa ekle (çok kritik)
    if "tn_prev" in data_for_plot.columns:
        fmt["tn_prev"] = format_euro

    if "agm_prev" in data_for_plot.columns:
        fmt["agm_prev"] = format_euro

    if "Δ AGM" in data_for_plot.columns:
        fmt["Δ AGM"] = format_euro

    
    if "Δ TN" in data_for_plot.columns:
        fmt["Δ TN"] = format_euro

    
    if "COGS (€)_prev" in data_for_plot.columns:
        fmt["COGS (€)_prev"] = format_euro

    if "VCE (€)_prev" in data_for_plot.columns:
        fmt["VCE (€)_prev"] = format_euro

    if "Δ COGS" in data_for_plot.columns:
        fmt["Δ COGS"] = format_euro

    if "Δ VCE" in data_for_plot.columns:
        fmt["Δ VCE"] = format_euro


    if "Δ VAR" in data_for_plot.columns:
        fmt["Δ VAR"] = format_euro

    if "margin_prev (AGM%)" in data_for_plot.columns:
        fmt["margin_prev (AGM%)"] = "{:.1f}%"

    if "Δ margin (AGM%)" in data_for_plot.columns:
        fmt["Δ margin (AGM%)"] = "{:+.1f} pp"
    column_order = [
        "pn",
        "family","customer","product", "Customer Count",
        "units",

        
        f"TN ({scen_1})", f"TN ({scen_2})", "Δ TN",
        f"COGS ({scen_1})", f"COGS ({scen_2})", "Δ COGS",
        f"VCE ({scen_1})", f"VCE ({scen_2})", "Δ VCE",
        f"AGM ({scen_1})", f"AGM ({scen_2})", "Δ AGM",
        f"VAR ({scen_1})", f"VAR ({scen_2})", "Δ VAR",


        "margin (AGM%)", "margin_prev (AGM%)", "Δ margin (AGM%)",

        "unit_tn", "unit_cogs", "unit_vce", "unit_agm", "unit_var"
    ]
    # ✅ DISPLAY rename (en sonda yapılır)
    data_for_plot = data_for_plot.rename(columns={
        "tn": f"TN ({scen_1})",
        "agm": f"AGM ({scen_1})",
        "cogs": f"COGS ({scen_1})",
        "vce": f"VCE ({scen_1})",
        "tn_prev": f"TN ({scen_2})",
        "agm_prev": f"AGM ({scen_2})",
        "cogs_prev": f"COGS ({scen_2})",
        "vce_prev": f"VCE ({scen_2})",
        "var": f"VAR ({scen_1})",
        "var_prev": f"VAR ({scen_2})",
    })
    data_for_plot = data_for_plot[
        [c for c in column_order if c in data_for_plot.columns]
    ]
    # ✅ style uygula
    styled = data_for_plot.style.format(fmt)
    def color_delta(val, col):

        try:
            val = float(val)
        except:
            return ""

        # TN & AGM → iyi = yüksek
        if col in ["Δ TN", "Δ AGM"]:
            if val > 0:
                return "background-color:#dcfce7"
            elif val < 0:
                return "background-color:#fee2e2"

        # COST → ters
        if col in ["Δ COGS", "Δ VCE"]:
            if val > 0:
                return "background-color:#fee2e2"
            elif val < 0:
                return "background-color:#dcfce7"

        # margin
        if col == "Δ margin (AGM%)":
            if val > 0:
                return "background-color:#dcfce7"
            elif val < 0:
                return "background-color:#fee2e2"
            
        if col == "Δ VAR":
            if val < 0:
                return "background-color:#dcfce7"
            elif val > 0:
                return "background-color:#fee2e2"

        return ""
    
    styled = styled.apply(
        lambda row: [color_delta(row[col], col) for col in row.index],
        axis=1
    )


   
    # ✅ önce hesapla (DIŞARIDA)
    cogs_cols = [c for c in data_for_plot.columns if "COGS" in c]
    vce_cols = [c for c in data_for_plot.columns if "VCE" in c]

    cogs_text = ""
    if cogs_cols:
        cogs_text = f"• COGS: {format_euro(data_for_plot[cogs_cols[0]].min())} → {format_euro(data_for_plot[cogs_cols[0]].max())}"

    vce_text = ""
    if vce_cols:
        vce_text = f"• VCE: {format_euro(data_for_plot[vce_cols[0]].min())} → {format_euro(data_for_plot[vce_cols[0]].max())}"

    

    # ✅ sonra caption BAS
    st.caption(f"""
    📊 Color Scale:

    • Margin (AGM%): {data_for_plot['margin (AGM%)'].min():.1f}% → {data_for_plot['margin (AGM%)'].max():.1f}%  
    {cogs_text}  
    {vce_text}

    👉 Colors are normalized per column (min → max)
    """)


    st.dataframe(styled, use_container_width=True)
    # ======================
    # TOP PRODUCTS
    # ======================
    top_products = (
        data_for_plot.sort_values(f"TN ({scen_1})", ascending=False)
        .head(5)
    )

    st.subheader("🏆 Top 5 Products by TN")

    top_products_display = top_products[[
        "product", f"TN ({scen_1})", f"AGM ({scen_1})", "margin (AGM%)"
    ]].style.format({
        f"TN ({scen_1})": format_euro,
        f"AGM ({scen_1})": format_euro,
        "margin (AGM%)": "{:.1f}%"
    })

    top_products_display = top_products_display.background_gradient(
        subset=["margin (AGM%)"],
        cmap="Pastel1"
    )

    st.dataframe(top_products_display, use_container_width=True)

    # ======================
    # FAMILY PERFORMANCE
    # ======================
    family_perf = (
        data_for_plot.groupby("family")[[f"TN ({scen_1})", f"AGM ({scen_1})"]]
        .sum()
    )

    family_perf["margin (AGM%)"] = (
        family_perf[f"AGM ({scen_1})"] / family_perf[f"TN ({scen_1})"].replace(0, 1)
    ) * 100

    family_perf = family_perf.sort_values(f"TN ({scen_1})", ascending=False)

    st.subheader("📊 Family Performance")

    family_perf_display = family_perf.style.format({
        f"TN ({scen_1})": format_euro,
        f"AGM ({scen_1})": format_euro,
        "margin (AGM%)": "{:.1f}%"
    })
    
    family_perf_display = family_perf_display.background_gradient(
        subset=["margin (AGM%)"],
        cmap="Pastel1"
    )

    st.dataframe(family_perf_display, use_container_width=True)

    # ======================
    # PN DETAIL
    # ======================
    st.subheader("🔍 PN Detail")

    pn_list = data_for_plot["pn"].unique().tolist()
        
    if len(pn_list) == 0:
        st.warning("No data for selected filters")
        return

    selected_pn = st.selectbox("Select PN", pn_list)

    row = data_for_plot[data_for_plot["pn"] == selected_pn].iloc[0] 

    st.write("### Unit Breakdown")
    st.write(f"### PN: {selected_pn}")
    if df_2 is not None and selected_pn in pn_2_detail.index:

        row_bdg = pn_2_detail.loc[selected_pn]

        pn_detail_df = pd.DataFrame({
            "Metric": ["TN", "COGS", "VCE", "AGM", "VAR", "AGM %"],

            
            "ACT (€)": [
                row[f"unit_tn"],
                row[f"unit_cogs"],
                row[f"unit_vce"],
                row[f"unit_agm"],
                row[f"unit_var"],
                row[f"unit_agm"] / row[f"unit_tn"] * 100 if row[f"unit_tn"] != 0 else 0,
            ],


            
            "BDG (€)": [
                row_bdg["unit_tn"],
                row_bdg["unit_cogs"],
                row_bdg["unit_vce"],
                row_bdg["unit_agm"],
                row_bdg["unit_var"],
                row_bdg["unit_agm"] / row_bdg["unit_tn"] * 100 if row_bdg["unit_tn"] != 0 else 0,
            ],

        })

        pn_detail_df["Δ (€)"] = (
            pn_detail_df["ACT (€)"] - pn_detail_df["BDG (€)"]
        )

    else:
        pn_detail_df = pd.DataFrame({
            "Metric": ["TN", "COGS", "VCE", "AGM", "VAR", "AGM %"],
            "ACT (€)": [
                row["unit_tn"],
                row["unit_cogs"],
                row["unit_vce"],
                row["unit_agm"],
                row["unit_var"],
                row["unit_agm"] / row["unit_tn"] * 100 if row["unit_tn"] != 0 else 0,
            ]
        })

   

    def style_pn_table(df):

        def apply_colors(row):
            styles = []

            metric = row["Metric"]

            for col in row.index:

                if col == "Metric":
                    styles.append("")
                    continue

                val = row[col]

                if "Δ" in col and isinstance(val, (int, float)):

                    # ✅ COGS → ters
                    if metric == "COGS":
                        if val < 0:
                            styles.append("background-color:#dcfce7")  # good
                        elif val > 0:
                            styles.append("background-color:#fee2e2")  # bad
                        else:
                            styles.append("")

                    # ✅ VAR → ters
                    elif metric == "VAR":
                        if val < 0:
                            styles.append("background-color:#dcfce7")
                        elif val > 0:
                            styles.append("background-color:#fee2e2")
                        else:
                            styles.append("")

                    # ✅ diğerleri (TN, AGM, VCE)
                    else:
                        if val > 0:
                            styles.append("background-color:#dcfce7")
                        elif val < 0:
                            styles.append("background-color:#fee2e2")
                        else:
                            styles.append("")
                else:
                    styles.append("")

            return styles

        styled = df.style.apply(apply_colors, axis=1)

        # ✅ format
        for col in df.columns:
            if "€" in col:
                styled = styled.format({col: format_euro})
            elif "%" in col:
                styled = styled.format({col: "{:.1f}%"})

        return styled


    styled_pn = style_pn_table(pn_detail_df)

    st.dataframe(styled_pn, use_container_width=True)
    


    