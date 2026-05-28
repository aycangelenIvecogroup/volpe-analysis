import streamlit as st
import pandas as pd
from pathlib import Path

# ==================================================
# PATH
# ==================================================
BASE_PATH = Path(__file__).resolve().parent.parent / "data"

FILES = {
    "ACT": BASE_PATH / "clean excel files" / "c04_2026_clean.xlsx",
    "BDG": BASE_PATH / "clean excel files" / "BDG2026_v4_clean.xlsx",
    "FCST": BASE_PATH / "clean excel files" / "fcst1_2026_clean.xlsx",
    "LY": BASE_PATH / "clean excel files" / "LY25_clean.xlsx"
}

# ==================================================
# CLEAN
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
# LOAD DATA
# ==================================================
@st.cache_data
def load_all():

    all_df = []

    for scen, path in FILES.items():

        df = pd.read_excel(path)
        df = clean_columns(df)

        df = df.rename(columns={
            "CUSTOMER MERGE": "customer",
            "FAMILY": "family",
            "PRODUCT": "product",
            "PN ALLESTIMENTO": "pn",
            "UNITS": "units",
            "TN": "tn",
            "COGS": "cogs",
            "VCE": "vce",
            "SGM": "sgm",
            "AGM": "agm"
        })

        for c in ["units", "tn", "cogs", "vce", "sgm", "agm"]:
            if c not in df.columns:
                df[c] = 0

        df["SCENARIO"] = scen
        all_df.append(df)

    df = pd.concat(all_df, ignore_index=True)

    for c in ["units", "tn", "cogs", "vce", "sgm", "agm"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    return df


# ==================================================
# COLOR LOGIC
# ==================================================
def color_logic(row):

    styles = []

    # Metric adı güvenli şekilde al
    metric = row.get("Metric", None)

    # Eğer Metric yoksa → index kullan
    if metric is None:
        metric = row.name

    inverted = ["COGS", "VAR"]

    for col in row.index:

        if "Δ" not in col:
            styles.append("")
            continue

        val = row[col]

        positive_good = metric not in inverted

        if val > 0:
            styles.append("color: green; font-weight: bold;" if positive_good else "color: red; font-weight: bold;")
        elif val < 0:
            styles.append("color: red; font-weight: bold;" if positive_good else "color: green; font-weight: bold;")
        else:
            styles.append("")

    return styles


# ==================================================
# UNIT TABLE
# ==================================================
def build_unit_table(df_group, scenarios):

    def calc(row):
        u = row["units"] if row["units"] != 0 else 1
        unit_price = row["tn"] / u
        unit_cogs = row["cogs"] / u
        unit_vce = row["vce"] / u
        unit_agm = row["agm"] / u
        unit_var = unit_price - unit_cogs - unit_vce - unit_agm

        return pd.Series({
            "Unit Price": unit_price,
            "COGS": unit_cogs,
            "VCE": unit_vce,
            "VAR": unit_var,
            "AGM": unit_agm
        })

    unit_df = df_group.apply(calc, axis=1)

    rows = []

    for metric in unit_df.columns:
        row = {"Metric": metric}

        for s in scenarios:
            row[s] = unit_df.loc[s][metric] if s in unit_df.index else 0

        for s in scenarios:
            if s != "ACT":
                row[f"Δ vs {s}"] = row["ACT"] - row[s]

        rows.append(row)

    res = pd.DataFrame(rows)

    return res


# ==================================================
# TOTAL TABLE
# ==================================================
def build_total_table(df_group, scenarios):

    def get(s, col):
        return df_group.loc[s, col] if s in df_group.index else 0

    rows = []

    for s in scenarios:
        tn = get(s, "tn")

    base = {}

    for s in scenarios:
        tn = get(s, "tn")
        cogs = get(s, "cogs")
        vce = get(s, "vce")
        agm = get(s, "agm")

        var = tn - cogs - vce - agm
        sgm = agm + var

        base[s] = {
            "UNITS": get(s, "units"),
            "TN": tn,
            "COGS": cogs,
            "VCE": vce,
            "VAR": var,
            "AGM": agm,
            "SGM": sgm,
            "AGM %": (agm / tn * 100) if tn != 0 else 0,
            "SGM %": (sgm / tn * 100) if tn != 0 else 0,
            "VAR %": (var / tn * 100) if tn != 0 else 0,
        }

    metrics = list(base["ACT"].keys())

    for m in metrics:
        row = {"Metric": m}

        for s in scenarios:
            row[s] = base[s][m]

        for s in scenarios:
            if s != "ACT":
                row[f"Δ vs {s}"] = row["ACT"] - row[s]

        rows.append(row)

    return pd.DataFrame(rows)


# ==================================================
# DISPLAY
# ==================================================
def show_table(df):

    df = df.copy()

    # =========================
    # UNIT TABLE MI?
    # =========================
    is_unit = df["Metric"].astype(str).str.contains("Unit").any()

    # =========================
    # BUILD FORMAT DICT
    # =========================
    format_dict = {}

    for col in df.columns:

        if col == "Metric":
            continue

        # ✅ yüzde kolonları
        if "%" in col:
            format_dict[col] = "{:.2f} %"

        # ✅ delta kolonları
        elif "Δ" in col:

            # metric bazlı % delta (pp)
            if df["Metric"].astype(str).str.contains("%").any():
                format_dict[col] = "{:+.2f} pp"
            else:
                format_dict[col] = "{:+,.0f}"

        # ✅ unit table
        elif is_unit:
            format_dict[col] = "{:,.2f}"

        # ✅ normal total values
        else:
            format_dict[col] = "{:,.0f}"

    # =========================
    # STYLE APPLY
    # =========================
    styled = df.style \
        .format(format_dict) \
        .apply(color_logic, axis=1) \
        .apply(delta_background, axis=1) \
        .set_properties(**{
            'font-size': '14px',
            'padding': '6px 10px'
        }) \
        .set_properties(subset=["Metric"], **{
            'text-align': 'left',
            'font-weight': 'bold'
        }) \
        .set_table_styles([
            {
                'selector': 'th',
                'props': [
                    ('text-align', 'center'),
                    ('font-weight', 'bold'),
                    ('font-size', '15px')
                ]
            }
        ])

    st.dataframe(styled, use_container_width=True)

def delta_background(row):

    styles = []

    for col in row.index:

        if "Δ" not in col:
            styles.append("")
            continue

        val = row[col]

        if val > 0:
            styles.append("background-color: #e6ffed;")
        elif val < 0:
            styles.append("background-color: #ffe6e6;")
        else:
            styles.append("")

    return styles



# ==================================================
# MAIN PAGE
# ==================================================
def render():

    st.title("🔥 Full P&L Analyzer")

    df = load_all()

    # ===============================
    # SCENARIO SELECT
    # ===============================
    scenarios = ["ACT"] + st.multiselect(
        "Compare with",
        ["BDG", "FCST", "LY"],
        default=["BDG"]
    )

    # ===============================
    # CUSTOMER
    # ===============================
    customer = st.multiselect(
        "Customer",
        df["customer"].dropna().unique()
    )

    d0 = df[df["customer"].isin(customer)]

    levels = [
        ("CUSTOMER", []),
        ("FAMILY", ["family"]),
        ("PRODUCT", ["family", "product"]),
        ("PN", ["family", "product", "pn"]),
    ]

    current_df = d0.copy()

    # ===============================
    # LOOP LEVELS
    # ===============================
    for level_name, group_cols in levels:

        st.markdown(f"## 🔹 {level_name}")

        if group_cols:
            options = current_df[group_cols[-1]].dropna().unique()
            selected = st.multiselect(level_name, options)
            if selected:
                current_df = current_df[current_df[group_cols[-1]].isin(selected)]

        df_group = current_df.groupby("SCENARIO")[[
            "units", "tn", "cogs", "vce", "sgm", "agm"
        ]].sum()

        # ===============================
        # UNIT TABLE
        # ===============================
        st.subheader("Unit Table")
        unit_table = build_unit_table(df_group, scenarios)
        show_table(unit_table)

        # ===============================
        # TOTAL TABLE
        # ===============================
        st.subheader("Total (No Unit)")
        total_table = build_total_table(df_group, scenarios)
        show_table(total_table)

        st.divider()


# ==================================================
if __name__ == "__main__":
    render()