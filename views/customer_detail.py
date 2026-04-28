import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
from openpyxl.styles import Font


# -----------------------------
# HELPERS
# -----------------------------
def fmt_amount(x):
    if pd.isna(x):
        return "–"
    if abs(x) >= 1_000_000:
        return f"{x/1_000_000:.1f} M"
    elif abs(x) >= 1_000:
        return f"{x/1_000:.0f} K"
    else:
        return f"{x:,.0f}"


# -----------------------------
# LOAD DATA (CACHED)
# -----------------------------
@st.cache_data
def load_data():
    # ZATEN ÇALIŞAN CLEAN DOSYA
    return pd.read_excel("customer_amount_layer_clean.xlsx")


# -----------------------------
# PAGE RENDER
# -----------------------------
def render_customer_detail(controls):

    st.title("📋 Customer Detail")
    st.caption("Customer-level performance vs target")
    st.divider()

    df = load_data()

    # -----------------------------
    # CONTROLS FROM SIDEBAR
    # -----------------------------
    month = controls.get("month", "March")
    scenario = controls.get("scenario", "ACT")
    critical_below = controls.get("critical_below", 70)
    warning_below = controls.get("warning_below", 90)

    # -----------------------------
    # SCENARIO → COLUMN MAP
    # -----------------------------
    if scenario == "ACT":
        agm_col = f"{month}_AGM%"
        tn_col = f"{month}_TN"
        coverage_col = f"{month}_Coverage_vs_B26%"
        gap_col = f"GAP_{month}_vs_B26_AGM%"
    elif scenario == "B26":
        agm_col = "B26_AGM%"
        tn_col = "B26_TN"
        coverage_col = None
        gap_col = None
    else:
        agm_col = f"{scenario}_AGM%"
        tn_col = f"{scenario}_TN"
        coverage_col = f"{scenario}_Coverage_vs_B26%"
        gap_col = f"GAP_{scenario}_vs_B26_AGM%"

    # -----------------------------
    # CUSTOMER SELECT
    # -----------------------------
    customer = st.selectbox(
        "Select Customer",
        sorted(df["CUSTOMER MERGE"].dropna().unique())
    )

    row = df[df["CUSTOMER MERGE"] == customer].iloc[0]

    # -----------------------------
    # RISK LOGIC
    # -----------------------------
    if coverage_col and coverage_col in df.columns:
        cov = row[coverage_col]

        if pd.isna(cov):
            risk = "–"
        elif cov < critical_below:
            risk = "CRITICAL"
        elif cov < warning_below:
            risk = "WARNING"
        else:
            risk = "OK"
    else:
        risk = "–"

    # -----------------------------
    # SNAPSHOT
    # -----------------------------
    st.markdown(
        f"""
        **Customer:** {customer}  
        **Scenario:** {scenario}  
        **Month:** {month}  
        **Risk level:** **{risk}**
        """
    )

    st.divider()

    # -----------------------------
    # KPI VALUES
    # -----------------------------
    agm_actual = row.get(agm_col)
    tn_actual = row.get(tn_col)
    tn_bdg = row.get("B26_TN")
    agm_bdg = row.get("B26_AGM%")

    agm_gap = agm_actual - agm_bdg if pd.notna(agm_actual) and pd.notna(agm_bdg) else None
    tn_gap = tn_bdg - tn_actual if pd.notna(tn_bdg) and pd.notna(tn_actual) else None

    coverage = row.get(coverage_col) if coverage_col else None

    # -----------------------------
    # KPI CARDS (6)
    # -----------------------------
    k1, k2, k3, k4, k5, k6 = st.columns(6)

    k1.metric("AGM %", f"{agm_actual:.1f} %" if pd.notna(agm_actual) else "–")
    k2.metric("AGM % (Target)", f"{agm_bdg:.1f} %" if pd.notna(agm_bdg) else "–")
    k3.metric("AGM Gap", f"{agm_gap:+.1f} pp" if agm_gap is not None else "–")

    k4.metric("Net Sales (TN)", fmt_amount(tn_actual))
    k5.metric("To Target (TN)", fmt_amount(tn_gap))

    if coverage_col:
        k6.metric("Coverage", f"{coverage:.1f} %" if pd.notna(coverage) else "–")
    else:
        k6.metric("Coverage", "–")

    st.divider()

    # -----------------------------
    # UNDERLYING DATA (FORMATTED)
    # -----------------------------
    st.subheader("📄 Underlying Data")

    def format_value(col, val):
        if pd.isna(val):
            return "–"
        if col.endswith("%"):
            return f"{val:.1f}"
        if "TN" in col or "Units" in col:
            return fmt_amount(val)
        return f"{val:,.1f}" if isinstance(val, (int, float)) else val

    formatted = {
        k: format_value(k, v)
        for k, v in row.items()
    }

    underlying_df = (
        pd.DataFrame.from_dict(formatted, orient="index", columns=["Value"])
        .reset_index()
        .rename(columns={"index": "Metric"})
    )

    st.dataframe(underlying_df, use_container_width=True, height=420)

    st.divider()

    # -----------------------------
    # EXPORT TO EXCEL
    # -----------------------------
    st.subheader("📥 Export")

    snapshot_df = pd.DataFrame({
        "Metric": [
            "Customer", "Scenario", "Month", "Risk Level",
            "AGM %", "AGM Target %",
            "AGM Gap",
            "Net Sales (TN)", "TN Target",
        ],
        "Value": [
            customer, scenario, month, risk,
            f"{agm_actual:.1f} %" if pd.notna(agm_actual) else "–",
            f"{agm_bdg:.1f} %" if pd.notna(agm_bdg) else "–",
            f"{agm_gap:+.1f}" if agm_gap is not None else "–",
            fmt_amount(tn_actual),
            fmt_amount(tn_bdg),
        ]
    })

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        snapshot_df.to_excel(writer, index=False, sheet_name="Customer Snapshot")

    st.download_button(
        "📥 Download Customer Detail (Excel)",
        data=output.getvalue(),
        file_name=f"customer_detail_{customer}_{scenario}_{month}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )