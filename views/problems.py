import streamlit as st
import pandas as pd
from pathlib import Path

# ==================================================
# PATHS (CLOUD SAFE)
# ==================================================
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"

FEB_FILE = RAW_DATA_DIR / "raw_agm02.xlsx"
MAR_FILE = RAW_DATA_DIR / "raw_agm03.xlsx"
BDG_FILE = RAW_DATA_DIR / "raw_agm_c12_2025.xlsx"

# ==================================================
# LOAD DATA
# ==================================================
@st.cache_data
def load_data():
    
    return (
            pd.read_excel(FEB_FILE, engine="openpyxl"),
            pd.read_excel(MAR_FILE, engine="openpyxl"),
            pd.read_excel(BDG_FILE, engine="openpyxl"),
            pd.read_excel(RAW_DATA_DIR / "raw_fcs1_26.xlsx", engine="openpyxl"),
        )


# ==================================================
# PAGE
# ==================================================
def render_problems():

    st.title("🚨 Problems")
    st.caption("Customer-level comparison (Feb / Mar / Budget)")
    st.divider()

    feb, mar, bdg, fcs1 = load_data()

    # --------------------------------------------------
    # NORMALIZATION
    # --------------------------------------------------
    # ✅ ACT FILES
    for df in (feb, mar, bdg):
        df.columns = (
            df.columns.astype(str)
            .str.strip()
            .str.upper()
            .str.replace("  ", " ", regex=False)
        )

        df["CUSTOMER MERGE"] = (
            df["CUSTOMER MERGE"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        for c in ["ACT UNITS", "ACT TN", "ACT COGS"]:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)


    # ✅ FCS1 (AYRI BLOK)
    fcs1.columns = (
        fcs1.columns.astype(str)
        .str.strip()
        .str.upper()
        .str.replace("  ", " ", regex=False)
    )

    fcs1["CUSTOMER MERGE"] = (
        fcs1["CUSTOMER MERGE"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    for c in ["FY UNITS", "FY TN", "FY COGS"]:
        fcs1[c] = pd.to_numeric(fcs1[c], errors="coerce").fillna(0)


    # --------------------------------------------------
    # AGGREGATION
    # --------------------------------------------------
    feb_agg = feb.groupby("CUSTOMER MERGE", as_index=False).agg(
        FEB_UNITS=("ACT UNITS", "sum"),
        FEB_TN=("ACT TN", "sum"),
        FEB_COGS=("ACT COGS", "sum"),
    )

    mar_agg = mar.groupby("CUSTOMER MERGE", as_index=False).agg(
        MAR_UNITS=("ACT UNITS", "sum"),
        MAR_TN=("ACT TN", "sum"),
        MAR_COGS=("ACT COGS", "sum"),
    )

    bdg_agg = bdg.groupby("CUSTOMER MERGE", as_index=False).agg(
        BDG_UNITS=("ACT UNITS", "sum"),
        BDG_TN=("ACT TN", "sum"),
        BDG_COGS=("ACT COGS", "sum"),
    )
    fcs1_agg = fcs1.groupby("CUSTOMER MERGE", as_index=False).agg(
        FCS1_UNITS=("FY UNITS", "sum"),
        FCS1_TN=("FY TN", "sum"),
        FCS1_COGS=("FY COGS", "sum"),
    )

    # --------------------------------------------------
    # MERGE
    # --------------------------------------------------
    df = (
        feb_agg
        .merge(mar_agg, on="CUSTOMER MERGE", how="left")
        .merge(bdg_agg, on="CUSTOMER MERGE", how="left")
        .merge(fcs1_agg, on="CUSTOMER MERGE", how="left")
    )

    # --------------------------------------------------
    # UNIT METRICS
    # --------------------------------------------------
    df["FEB_PRICE"] = df["FEB_TN"] / df["FEB_UNITS"]
    df["FEB_COST"] = df["FEB_COGS"] / df["FEB_UNITS"]

    df["MAR_PRICE"] = df["MAR_TN"] / df["MAR_UNITS"]
    df["MAR_COST"] = df["MAR_COGS"] / df["MAR_UNITS"]

    df["BDG_PRICE"] = df["BDG_TN"] / df["BDG_UNITS"]
    df["BDG_COST"] = df["BDG_COGS"] / df["BDG_UNITS"]

    df["FCS1_PRICE"] = df["FCS1_TN"] / df["FCS1_UNITS"]
    df["FCS1_COST"] = df["FCS1_COGS"] / df["FCS1_UNITS"]

    # --------------------------------------------------
    # DELTAS
    # --------------------------------------------------
    df["Δ TN (MAR - FEB)"] = df["MAR_TN"] - df["FEB_TN"]
    df["Δ COST (MAR - FEB)"] = df["MAR_COST"] - df["FEB_COST"]
    df["Δ PRICE (MAR - FEB)"] = df["MAR_PRICE"] - df["FEB_PRICE"]

    df["Δ TN (MAR - BDG)"] = df["MAR_TN"] - df["BDG_TN"]
    df["Δ COST (MAR - BDG)"] = df["MAR_COST"] - df["BDG_COST"]
    df["Δ PRICE (MAR - BDG)"] = df["MAR_PRICE"] - df["BDG_PRICE"]

    df["Δ TN (MAR - FCS1)"] = df["MAR_TN"] - df["FCS1_TN"]
    df["Δ COST (MAR - FCS1)"] = df["MAR_COST"] - df["FCS1_COST"]
    df["Δ PRICE (MAR - FCS1)"] = df["MAR_PRICE"] - df["FCS1_PRICE"]

    # --------------------------------------------------
    # FILTERS
    # --------------------------------------------------
    customers = st.multiselect(
        "Customer",
        sorted(df["CUSTOMER MERGE"].unique())
    )

    if customers:
        df = df[df["CUSTOMER MERGE"].isin(customers)]
    def detect_problem(row):
        parts = []

        # COST
        if row["MAR_COST"] > row["BDG_COST"]:
            parts.append('<span style="color:red;">Cost ↑</span>')
        elif row["MAR_COST"] < row["BDG_COST"]:
            parts.append('<span style="color:green;">Cost ↓</span>')

        # PRICE
        if row["MAR_PRICE"] > row["BDG_PRICE"]:
            parts.append('<span style="color:green;">Price ↑</span>')
        elif row["MAR_PRICE"] < row["BDG_PRICE"]:
            parts.append('<span style="color:red;">Price ↓</span>')

        return " & ".join(parts)
    
    def detect_problem_fcs1(row):
        parts = []

        # COST
        if row["MAR_COST"] > row["FCS1_COST"]:
            parts.append('<span style="color:red;">Cost ↑</span>')
        elif row["MAR_COST"] < row["FCS1_COST"]:
            parts.append('<span style="color:green;">Cost ↓</span>')

        # PRICE
        if row["MAR_PRICE"] > row["FCS1_PRICE"]:
            parts.append('<span style="color:green;">Price ↑</span>')
        elif row["MAR_PRICE"] < row["FCS1_PRICE"]:
            parts.append('<span style="color:red;">Price ↓</span>')

        return " & ".join(parts)
    # --------------------------------------------------
    # DISPLAY
    # --------------------------------------------------
    default_columns = [
        "CUSTOMER MERGE",
        "MAR_TN", "MAR_PRICE", "MAR_COST",
        "BDG_PRICE", "BDG_COST",
        "Δ COST (MAR - BDG)",
        "Δ PRICE (MAR - BDG)",
    ]

    display_df = df[default_columns].sort_values(
        "Δ COST (MAR - BDG)", ascending=False
    )
    display_df["Problem"] = display_df.apply(detect_problem, axis=1)

    def format_euro(x):
        if pd.isna(x):
            return ""
        if abs(x) >= 1_000_000:
            return f"€ {x/1_000_000:.1f}M"
        elif abs(x) >= 1_000:
            return f"€ {x/1_000:.1f}K"
        else:
            return f"€ {x:.0f}"

    def style_table(df):

        format_dict = {}

        for col in df.columns:
            col_lower = col.lower()

            # ✅ price / cost (unit değerler)
            if "price" in col_lower or "cost" in col_lower:
                format_dict[col] = "€ {:.0f}"

            # ✅ TN (total)
            elif "tn" in col_lower:
                format_dict[col] = format_euro

        return df.style.format(format_dict)
    
    def color_problem_text(val):
        text = str(val)

        # 🔴 BAD CASES
        if "Cost ↑" in text and "Price ↓" in text:
            return "color: red; font-weight: bold"

        # 🟢 BEST CASE
        if "Cost ↓" in text and "Price ↑" in text:
            return "color: green; font-weight: bold"

        # MIXED CASES
        if "Cost ↑" in text:
            return "color: red"
        if "Price ↓" in text:
            return "color: red"

        if "Cost ↓" in text:
            return "color: green"
        if "Price ↑" in text:
            return "color: green"

        return ""

    
    def highlight_delta(val, col_name):
        try:
            val = float(val)

            # COST → ters logic
            if "COST" in col_name:
                if val > 0:
                    return "color: red"
                elif val < 0:
                    return "color: green"

            # PRICE → normal logic
            elif "PRICE" in col_name:
                if val > 0:
                    return "color: green"
                elif val < 0:
                    return "color: red"

        except:
            pass

        return ""

    
    styled = style_table(display_df)
    
  
    # Apply delta text coloring
    delta_cols = [col for col in display_df.columns if "Δ" in col or "∆" in col]
    if delta_cols:
        for col in delta_cols:
            styled = styled.map(lambda v: highlight_delta(v, col), subset=[col])

    
    # Align: customer column left, numbers right
    styled = styled.set_properties(**{"text-align": "right"})
    styled = styled.set_properties(subset=["CUSTOMER MERGE"], **{"text-align": "left"})

    st.markdown(
        styled.to_html(escape=False),
        unsafe_allow_html=True
    )
    st.divider()
    st.subheader("📊 ACT vs FCS1")  
    
    fcs1_columns = [
        "CUSTOMER MERGE",
        "MAR_TN", "MAR_PRICE", "MAR_COST",
        "FCS1_PRICE", "FCS1_COST",
        "Δ COST (MAR - FCS1)",
        "Δ PRICE (MAR - FCS1)",
    ]

    fcs1_df = df[fcs1_columns] \
        .sort_values("Δ COST (MAR - FCS1)", ascending=False) \
        .copy()


    fcs1_df["Problem"] = fcs1_df.apply(detect_problem_fcs1, axis=1)

    # ✅ Problem column'u öne al (BDG tablosu gibi)
    fcs1_df = fcs1_df[
        [col for col in fcs1_df.columns if col != "Problem"] + ["Problem"]
    ]

    styled_fcs1 = style_table(fcs1_df)

    # delta coloring aynen uygula
    delta_cols_fcs1 = [col for col in fcs1_df.columns if "Δ" in col]

    for col in delta_cols_fcs1:
        styled_fcs1 = styled_fcs1.map(
            lambda v: highlight_delta(v, col),
            subset=[col]
        )

    # alignment
    styled_fcs1 = styled_fcs1.set_properties(**{"text-align": "right"})
    styled_fcs1 = styled_fcs1.set_properties(
        subset=["CUSTOMER MERGE"],
        **{"text-align": "left"}
    )

    # HTML render (renkli text için)
    st.markdown(
        styled_fcs1.to_html(escape=False),
        unsafe_allow_html=True
    )

