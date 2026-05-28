import pandas as pd
import numpy as np
import streamlit as st

from scenario_data_loader import load_all_data

# -----------------------
# CONFIG
# -----------------------

KPI_ALL = ["units","tn","cogs","vce","sgm","agm","var","price","cost"]

GROUP_MAP = {
    "Customer": ["customer_merge"],
    "Family": ["customer_merge","family"],
    "Product": ["customer_merge","family","product"],
    "PN": ["customer_merge","family","product","plant","pn_allestimento"]
}

# -----------------------
# ENRICH
# -----------------------

def enrich(df):
    df = df.copy()

    df["var"] = df["tn"] - df["cogs"] - df["vce"] - df["agm"]
    df["price"] = np.where(df["units"]!=0, df["tn"]/df["units"],0)
    df["cost"]  = np.where(df["units"]!=0, df["cogs"]/df["units"],0)

    return df

# -----------------------
# FORMAT + COLOR
# -----------------------

def format_df(df):
    df = df.copy()

    for col in df.columns:
        num = pd.to_numeric(df[col], errors="coerce")

        if num.notna().any():

            if "Δ" in col:
                df[col] = num.map(lambda x: f"{x:.1f} pp")
            elif "%" in col:
                df[col] = num.map(lambda x: f"{x:.1f}%")
            else:
                df[col] = num.map(lambda x: f"{x:,.0f}")

    return df


def highlight(df):
    df = df.copy()

    for col in df.columns:
        if "Δ" in col or (len(df) > 0 and "pp" in str(df[col].iloc[0])):

            reverse = any(x in col for x in ["cogs","price"])

            def style(val):
                try:
                    v = float(str(val).replace(",","").replace("%","").replace("pp",""))
                except:
                    return ""

                if v == 0:
                    return ""

                if reverse:
                    color = "red" if v>0 else "green"
                else:
                    color = "green" if v>0 else "red"

                return f"color:{color}; font-weight:bold"

            df[col] = df[col].map(lambda x: f"<span style='{style(x)}'>{x}</span>")

    return df

# -----------------------
# MAIN
# -----------------------

def render_scenario_builder():

    st.title("Scenario Builder 🚀")

    df = load_all_data()
    df = enrich(df)

    # -----------------------
    # FILTERS
    # -----------------------

    customers = st.multiselect("Customer", sorted(df["customer_merge"].dropna().unique()))
    families = st.multiselect("Family", sorted(df["family"].dropna().unique()))
    products = st.multiselect("Product", sorted(df["product"].dropna().unique()))
    pns = st.multiselect("PN", sorted(df["pn_allestimento"].dropna().unique()))

    kpis = st.multiselect("KPIs", KPI_ALL, default=["agm"])

    level = st.selectbox("Aggregation Level", list(GROUP_MAP.keys()))

    f = df.copy()

    if customers:
        f = f[f["customer_merge"].isin(customers)]
    if families:
        f = f[f["family"].isin(families)]
    if products:
        f = f[f["product"].isin(products)]
    if pns:
        f = f[f["pn_allestimento"].isin(pns)]

    
    st.markdown("""
    <style>

    table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        font-size: 13px;
        border-radius: 10px;
        overflow: hidden;
    }

    
    th {
        background: linear-gradient(90deg, #eef1f7, #e3e7ef);
        text-align: center;
        padding: 10px;
        font-weight: 600;
        border-bottom: 2px solid #dcdcdc;
    }


    td {
        padding: 8px;
        border-bottom: 1px solid #f1f1f1;
    }

    tr:hover {
        background-color: #f9fafc;
    }

    td:first-child {
        text-align: left;
        font-weight: 500;
    }

    </style>
    """, unsafe_allow_html=True)

    # -----------------------
    # MAIN TABLE (pivot)
    # -----------------------

    group_cols = GROUP_MAP[level] + ["scenario"]
    valid_kpis = [k for k in kpis if k in f.columns]

    agg = f.groupby(group_cols, as_index=False)[valid_kpis].sum()

    df_final = agg.pivot_table(
        index=GROUP_MAP[level],
        columns="scenario",
        values=valid_kpis,
        fill_value=0
    )

    df_final.columns = [f"{k}_{s}" for k,s in df_final.columns]
    df_final = df_final.reset_index()

    for k in valid_kpis:
        if f"{k}_ACTUAL" in df_final.columns:
            df_final[f"{k}_Δ ACT-BDG"] = df_final[f"{k}_ACTUAL"] - df_final.get(f"{k}_BDG",0)

    st.subheader("Main Table")
    st.markdown(highlight(format_df(df_final)).to_html(escape=False,index=False),
                unsafe_allow_html=True)
    

    base = f.groupby("scenario").agg({
        "tn": "sum",
        "agm": "sum",
        "sgm": "sum"
    })

    act = base.loc["ACTUAL"] if "ACTUAL" in base.index else None
    bdg = base.loc["BDG"] if "BDG" in base.index else None
    def safe_get(scen, col):
        return base.loc[scen, col] if scen in base.index else 0


    if act is not None and bdg is not None:

        agm_pct = act["agm"] / act["tn"] * 100 if act["tn"] else 0
        sgm_pct = act["sgm"] / act["tn"] * 100 if act["tn"] else 0

        agm_delta = (act["agm"]/act["tn"] - bdg["agm"]/bdg["tn"]) * 100
        sgm_delta = (act["sgm"]/act["tn"] - bdg["sgm"]/bdg["tn"]) * 100

    # -----------------------
    # KPI
    # -----------------------
    st.markdown("""
    <style>
    .kpi-card {
        padding: 15px;
        border-radius: 10px;
        background-color: #f7f7f7;
        text-align: center;
        margin-bottom:10px;
    }

    .kpi-value {
        font-size: 30px;
        font-weight: bold;
    }

    .delta-pos { color: green; font-weight: bold; }
    .delta-neg { color: red; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)
    def kpi_card(title, value, delta):
        color = "delta-pos" if delta > 0 else "delta-neg"
        arrow = "▲" if delta > 0 else "▼"

        return f"""
        <div class="kpi-card">
            <div>{title}</div>
            <div class="kpi-value">{value:.1f}%</div>
            <div class="{color}">{arrow} {delta:.1f} pp</div>
        </div>
        """

    col1, col2 = st.columns(2)

    if act is not None and bdg is not None:

        col1, col2 = st.columns(2)

        col1.markdown(kpi_card("AGM", agm_pct, agm_delta), unsafe_allow_html=True)
        col2.markdown(kpi_card("SGM", sgm_pct, sgm_delta), unsafe_allow_html=True)

    else:
        st.info("KPI data not available")


    # -----------------------
    # PERCENTAGES
    # -----------------------

    rows = []

    # base %
    for s in base.index:
        tn = base.loc[s, "tn"]

        rows.append({
            "Scenario": s,
            "AGM %": (base.loc[s,"agm"]/tn*100) if tn else 0,
            "SGM %": (base.loc[s,"sgm"]/tn*100) if tn else 0,
        })

    def pp(a,b):
        return (a[0]/a[1] - b[0]/b[1]) * 100 if a[1] and b[1] else 0

    # deltas
    rows.append({
        "Scenario": "Δ ACT-BDG",
        "AGM %": pp((act["agm"],act["tn"]), (bdg["agm"],bdg["tn"])),
        "SGM %": pp((act["sgm"],act["tn"]), (bdg["sgm"],bdg["tn"]))
    })

    rows.append({
        "Scenario": "Δ ACT-FCS",
        "AGM %": pp((act["agm"],act["tn"]), (safe_get("FCS","agm"), safe_get("FCS","tn"))),
        "SGM %": pp((act["sgm"],act["tn"]), (safe_get("FCS","sgm"), safe_get("FCS","tn")))
    })

    rows.append({
        "Scenario": "Δ ACT-LY",
        "AGM %": pp((act["agm"],act["tn"]), (safe_get("LY","agm"), safe_get("LY","tn"))),
        "SGM %": pp((act["sgm"],act["tn"]), (safe_get("LY","sgm"), safe_get("LY","tn")))
    })

    pct_df = pd.DataFrame(rows)

    st.subheader("Percentages")
    st.markdown(highlight(format_df(pct_df)).to_html(escape=False,index=False),
                unsafe_allow_html=True)
    




    
    # -----------------------
    # TOP PRODUCTS
    # -----------------------

    act = f[f["scenario"]=="ACTUAL"]
    bdg = f[f["scenario"]=="BDG"]

    grp = ["product"] if not customers else ["customer_merge","product"]

    prod = act.groupby(grp,as_index=False)["agm"].sum()
    prod_bdg = bdg.groupby(grp,as_index=False)["agm"].sum()

    prod = prod.merge(prod_bdg,on=grp,how="left",suffixes=("_act","_bdg")).fillna(0)
    prod["Δ_agm"] = prod["agm_act"] - prod["agm_bdg"]

    top = prod.sort_values("Δ_agm", ascending=False).head(10)
    worst = prod.sort_values("Δ_agm").head(10)

    col1, col2 = st.columns(2)

    col1.write("Top Products")
    col1.markdown(highlight(format_df(top)).to_html(escape=False,index=False), unsafe_allow_html=True)

    col2.write("Worst Products")
    col2.markdown(highlight(format_df(worst)).to_html(escape=False,index=False), unsafe_allow_html=True)

    # ✅ driver insight
    if not top.empty and not worst.empty:

        best = top.iloc[0]
        worst_ = worst.iloc[0]

        
    st.markdown(f"""
    ### 🔍 Drivers Insight

    - 🟢 **Top driver:** {best.get('product','-')} (+{best['Δ_agm']:,.0f})
    - 🔴 **Worst driver:** {worst_.get('product','-')} ({worst_['Δ_agm']:,.0f})
    """)

    total_impact = prod["Δ_agm"].abs().sum()

    if not top.empty and total_impact > 0:

        best = top.iloc[0]
        contribution = best["Δ_agm"] / total_impact * 100

        st.caption(f"Top driver contributes {contribution:.1f}% of total change")


    # -----------------------
    # TOP FAMILIES
    # -----------------------

    grp = ["family"] if not customers else ["customer_merge","family"]

    fam = act.groupby(grp,as_index=False)["agm"].sum()
    fam_bdg = bdg.groupby(grp,as_index=False)["agm"].sum()

    fam = fam.merge(fam_bdg,on=grp,how="left",suffixes=("_act","_bdg")).fillna(0)
    fam["Δ_agm"] = fam["agm_act"] - fam["agm_bdg"]

    top = fam.sort_values("Δ_agm",ascending=False).head(10)
    worst = fam.sort_values("Δ_agm").head(10)

    col1,col2 = st.columns(2)

    col1.write("Top Families")
    col1.markdown(highlight(format_df(top)).to_html(escape=False,index=False),unsafe_allow_html=True)

    col2.write("Worst Families")
    col2.markdown(highlight(format_df(worst)).to_html(escape=False,index=False),unsafe_allow_html=True)



    st.subheader("PN Analysis")

    with st.expander("🔍 PN Details"):

        pn_grp = ["pn_allestimento"] if not customers else ["customer_merge","pn_allestimento"]

        # -----------------------
        # BASE
        # -----------------------

        pn_base = f.groupby(pn_grp + ["scenario"], as_index=False).agg({
            "agm": "sum",
            "tn": "sum",
            "cogs": "sum",
            "vce": "sum",
            "units": "sum"
        })

        # -----------------------
        # PIVOT
        # -----------------------

        pn = pn_base.pivot_table(
            index=pn_grp,
            columns="scenario",
            values=["agm","tn","cogs","vce","units"],
            fill_value=0
        )

        pn.columns = [f"{k}_{s}" for k, s in pn.columns]
        pn = pn.reset_index()

        # -----------------------
        # UNIT BASED METRICS ✅🔥
        # -----------------------

        for s in ["ACTUAL","BDG","FCS","LY"]:
            if f"tn_{s}" in pn.columns and f"units_{s}" in pn.columns:
                pn[f"price_unit_{s}"] = np.where(pn[f"units_{s}"] != 0, pn[f"tn_{s}"]/pn[f"units_{s}"], 0)

            if f"cogs_{s}" in pn.columns and f"units_{s}" in pn.columns:
                pn[f"cogs_unit_{s}"] = np.where(pn[f"units_{s}"] != 0, pn[f"cogs_{s}"]/pn[f"units_{s}"], 0)

            if f"vce_{s}" in pn.columns and f"units_{s}" in pn.columns:
                pn[f"vce_unit_{s}"] = np.where(pn[f"units_{s}"] != 0, pn[f"vce_{s}"]/pn[f"units_{s}"], 0)

            if f"agm_{s}" in pn.columns and f"units_{s}" in pn.columns:
                pn[f"agm_unit_{s}"] = np.where(pn[f"units_{s}"] != 0, pn[f"agm_{s}"]/pn[f"units_{s}"], 0)

        # -----------------------
        # DELTA VALUE
        # -----------------------

        if "agm_ACTUAL" in pn.columns:
            pn["agm_Δ ACT-BDG"] = pn["agm_ACTUAL"] - pn.get("agm_BDG", 0)

        # -----------------------
        # ✅ DRIVER INSIGHT
        # -----------------------

        if "agm_Δ ACT-BDG" in pn.columns and not pn.empty:

            best_pn = pn.sort_values("agm_Δ ACT-BDG", ascending=False).head(1)

            st.markdown(f"""
            ### 🔍 PN Driver Insight

            🟢 Top PN: {best_pn.iloc[0][pn_grp[-1]]}  
            Impact: {best_pn.iloc[0]['agm_Δ ACT-BDG']:,.0f}
            """)

        # -----------------------
        # ✅ MAIN PN TABLE
        # -----------------------

        st.markdown(highlight(format_df(pn)).to_html(escape=False,index=False),
                    unsafe_allow_html=True)

        # -----------------------
        # ✅ 🔥 SECOND TABLE (UNIT BASED)
        # -----------------------

        unit_cols = [c for c in pn.columns if "_unit_" in c]

        pn_unit = pn[pn_grp + unit_cols]

        st.markdown("### ⚖️ Unit-based Metrics")
        st.caption("All values are divided by units (€/unit) to show efficiency independent of volume")

        st.markdown(highlight(format_df(pn_unit)).to_html(escape=False,index=False),
                    unsafe_allow_html=True)
