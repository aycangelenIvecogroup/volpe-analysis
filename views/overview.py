import streamlit as st
import pandas as pd
from pathlib import Path

from ui.helpers import explain_overview


# ==================================================
# PATH CONFIG (CLOUD SAFE)
# ==================================================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "customer_amount_layer_clean.xlsx"


@st.cache_data
def load_data():
    return pd.read_excel(DATA_PATH)


def render_overview(controls):
    st.title("📊 Sales Risk Overview")
    st.caption("Identify where to act first based on risk definition and ranking focus.")
    st.divider()

    df = load_data()

    # -----------------------------
    # CONTROLS
    # -----------------------------
    month = controls["month"]
    scenario = controls["scenario"]
    rank_mode = controls["rank_mode"]
    critical_below = controls["critical_below"]
    warning_below = controls["warning_below"]

    # -----------------------------
    # SCENARIO → COLUMN MAPPING
    # -----------------------------
    if scenario == "ACT":
        agm_col = f"{month}_AGM%"
        coverage_col = f"{month}_Coverage_vs_B26%"
        gap_col = f"GAP_{month}_vs_B26_AGM%"

    elif scenario == "B26":
        agm_col = "B26_AGM%"
        coverage_col = None
        gap_col = None

    else:
        agm_col = f"{scenario}_AGM%"
        coverage_col = f"{scenario}_Coverage_vs_B26%"
        gap_col = f"GAP_{scenario}_vs_B26_AGM%"

    # -----------------------------
    # KPI SNAPSHOT
    # -----------------------------
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Avg AGM %", f"{df[agm_col].mean():.1f} %")

    if coverage_col:
        c2.metric("Avg Coverage", f"{df[coverage_col].mean():.1f} %")
        c3.metric(
            "Critical Customers",
            int((df[coverage_col] < critical_below).sum())
        )
        c4.metric("Worst Coverage", f"{df[coverage_col].min():.1f} %")
    else:
        c2.metric("Avg Coverage", "–")
        c3.metric("Critical Customers", "–")
        c4.metric("Worst Coverage", "–")

    # -----------------------------
    # TABLE PREPARATION
    # -----------------------------
    cols = ["CUSTOMER MERGE", agm_col]
    if coverage_col:
        cols.append(coverage_col)
    if gap_col:
        cols.append(gap_col)

    view_df = df[cols].copy()

    for c in cols:
        if c != "CUSTOMER MERGE":
            view_df[c] = pd.to_numeric(view_df[c], errors="coerce").round(1)

    # -----------------------------
    # RISK LOGIC
    # -----------------------------
    if coverage_col:
        def compute_risk(x):
            if x < critical_below:
                return "CRITICAL"
            elif x < warning_below:
                return "WARNING"
            else:
                return "OK"

        view_df["Risk"] = view_df[coverage_col].apply(compute_risk)

        if rank_mode == "Sales Execution (Coverage)":
            view_df = view_df.sort_values(coverage_col)
        else:
            view_df = view_df.sort_values(gap_col)
    else:
        view_df["Risk"] = "–"

    # -----------------------------
    # STYLE
    # -----------------------------
    def color_row(row):
        if row["Risk"] == "CRITICAL":
            return ["background-color:#fdecea"] * len(row)
        elif row["Risk"] == "WARNING":
            return ["background-color:#fff4e5"] * len(row)
        else:
            return ["background-color:#edf7ed"] * len(row)

    fmt = {agm_col: "{:.1f}"}
    if coverage_col:
        fmt[coverage_col] = "{:.1f}"
    if gap_col:
        fmt[gap_col] = "{:.1f}"

    st.dataframe(
        view_df
        .style
        .apply(color_row, axis=1)
        .format(fmt),
        height=520
    )

    st.divider()

    # -----------------------------
    # MANAGEMENT INTERPRETATION
    # -----------------------------
    st.subheader("🧠 Management Interpretation")
    for line in explain_overview(df, month, critical_below):
        st.write(f"- {line}")