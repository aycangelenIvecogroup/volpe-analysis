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
    col3, col4 = st.columns(2)

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
    pn_1 = df_1.groupby("pn").agg({
        "family": lambda x: x.mode()[0] if len(x.mode()) > 0 else "",
        "product": lambda x: x.mode()[0] if len(x.mode()) > 0 else "",
        "customer": "nunique",
        "units": "sum",
        "tn": "sum",
        "agm": "sum",
        "vce": "sum",
        "cogs": "sum"
    })

    pn_1 = pn_1.rename(columns={"customer": "Customer Count"})

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

    # ✅ margin artık açık
    pn_1["margin (AGM%)"] = (
        pn_1["agm"] / pn_1["tn"].replace(0, 1)
    ) * 100

    # ======================
    # KPI ROW
    # ======================
    colk1, colk2, colk3 = st.columns(3)

    colk1.metric("💰 TN (Turnover)", f"€ {pn_1['tn'].sum():,.0f}")
    colk2.metric("💰 AGM", f"€ {pn_1['agm'].sum():,.0f}")
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

    # ======================
    # COMPARISON
    # ======================
    if df_2 is not None:

        pn_2 = df_2.groupby("pn")[["tn", "agm"]].sum()

        pn_compare = pn_1.join(pn_2, how="left", rsuffix="_prev").fillna(0)

        pn_compare["Δ AGM"] = pn_compare["agm"] - pn_compare["agm_prev"]
        pn_compare["Δ TN"] = pn_compare["tn"] - pn_compare["tn_prev"]

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

    st.dataframe(
        data_for_plot.style.background_gradient(subset=["margin (AGM%)"], cmap="RdYlGn"),
        use_container_width=True
    )

    # ======================
    # PN DETAIL
    # ======================
    st.subheader("🔍 PN Detail")

    pn_list = data_for_plot.index.tolist()
    selected_pn = st.selectbox("Select PN", pn_list)

    row = data_for_plot.loc[selected_pn]

    st.write("### Unit Breakdown")

    st.write({
        "unit TN": row["unit_tn"],
        "unit COGS": row["unit_cogs"],
        "unit VCE": row["unit_vce"],
        "unit AGM": row["unit_agm"],
        "unit VAR": row["unit_var"]
    })

    # ======================
    # CHART
    # ======================
    st.subheader("📊 TN vs margin (AGM%)")

    fig, ax = plt.subplots()

    ax.scatter(
        data_for_plot["tn"],
        data_for_plot["margin (AGM%)"],
        s=data_for_plot["units"] / 10
    )

    ax.set_xlabel("TN (Turnover)")
    ax.set_ylabel("margin (AGM%)")

    st.pyplot(fig)