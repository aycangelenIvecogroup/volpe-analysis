import streamlit as st
import pandas as pd
from pathlib import Path
from io import BytesIO
# ==================================================
# PATH
# ==================================================
BASE_PATH = Path(__file__).resolve().parent.parent / "data"

FILES = {
    "ACT": BASE_PATH / "clean excel files" / "c05_2026_clean.xlsx",
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
        # CUSTOMER NORMALIZATION
        df["customer"] = (
            df["customer"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        df["customer"] = df["customer"].replace({
            "SDF": "SAME DEUTZ-FAHR DEUTSCHLAND GMBH",
            "ATLAS COPCO_NC": "ATLAS COPCO",
            "YANMAR ITALY": "YANMAR"
          
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

        try:
            val = float(str(row[col]).replace("pp","").replace("%","").replace(",",""))
        except:
            val = 0


        # ✅ string → number convert
        try:
            v = float(
                str(val)
                .replace(",", "")
                .replace("pp", "")
                .replace("%", "")
            )
        except:
            v = 0

        positive_good = metric not in inverted

        if v > 0:
            styles.append("color: green; font-weight: bold;" if positive_good else "color: red; font-weight: bold;")
        elif v < 0:
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
        unit_sgm = row["sgm"] / u
        unit_var = unit_price - unit_cogs - unit_vce - unit_agm

        return pd.Series({
            
            "COGS (€/unit)": unit_cogs,
            "VCE (€/unit)": unit_vce,
            "VAR (€/unit)": unit_var,
            "AGM (€/unit)": unit_agm,
            "SGM (€/unit)": unit_sgm,

            
            "AGM %": (unit_agm / unit_price * 100) if unit_price != 0 else 0,
            "VAR %": (unit_var / unit_price * 100) if unit_price != 0 else 0,
            "SGM %": (unit_sgm / unit_price * 100) if unit_price != 0 else 0,


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
    # ✅ total TN (mix için gerekli)
    total_tn = df_group["tn"].sum() if "tn" in df_group.columns else 0
    base = {}

    for s in scenarios:
        tn = get(s, "tn")
        cogs = get(s, "cogs")
        vce = get(s, "vce")
        agm = get(s, "agm")

        var = tn - cogs - vce - agm
        sgm = get(s, "sgm")

        base[s] = {
            "UNITS": get(s, "units"),
            "TN (€)": tn,
            "COGS(€)": cogs,
            "VCE(€)": vce,
            "VAR(€)": var,
            "AGM(€)": agm,
            "SGM(€)": sgm,
            "AGM %": (agm / tn * 100) if tn != 0 else 0,
            "SGM %": (sgm / tn * 100) if tn != 0 else 0,
            "VAR %": (var / tn * 100) if tn != 0 else 0,
            "MIX(tn/total_tn) %": (tn / total_tn * 100) if total_tn != 0 else 0,
        }

    metrics = list(base["ACT"].keys())

    for m in metrics:
        row = {"Metric": m}

        for s in scenarios:
            row[s] = base[s][m]

        
        for s in scenarios:
            if s != "ACT":

                delta = row["ACT"] - row[s]

                if "%" in m:
                    row[f"Δ vs {s}"] = delta   # pp
                else:
                    row[f"Δ vs {s}"] = delta


        rows.append(row)

    return pd.DataFrame(rows)

def to_excel(df):

    output = BytesIO()

    # ✅ kopya al (string delta bozmasın)
    df_export = df.copy()

    # ✅ delta kolonlarını temizle (pp, %, virgül kaldır)
    for col in df_export.columns:
        if "Δ" in col:
            df_export[col] = df_export[col].astype(str)\
                .str.replace("pp","")\
                .str.replace("%","")\
                .str.replace(",","")

    # ✅ Excel yaz
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_export.to_excel(writer, index=False, sheet_name="Sheet1")

    return output.getvalue()
# ==================================================
# DISPLAY
# ==================================================
def show_table(df):

    # ✅ metric yoksa oluştur
    if "Metric" not in df.columns:
        df["Metric"] = df.index

    df = df.copy()

    # ✅ DELTA FORMAT (pp vs €)
    for col in df.columns:
        if "Δ" in col:

            new_vals = []

            for v, m in zip(df[col], df["Metric"]):
                try:
                    v_num = float(v)
                except:
                    v_num = 0

                if "%" in str(m):
                    new_vals.append(f"{v_num:+.2f} pp")
                else:
                    new_vals.append(f"{v_num:+,.0f}")

            df[col] = new_vals

    # ✅ STYLE OBJECT
    styled = df.style

    # ✅ ROW-BASED FORMAT
    for i, metric in enumerate(df["Metric"]):

        row = df.index[i]

        # sadece numeric kolonlar
        numeric_cols = [c for c in df.columns if c != "Metric" and "Δ" not in c]

        if "%" in str(metric):
            styled = styled.format("{:.2f} %", subset=(row, numeric_cols))

        elif "€/unit" in str(metric):
            styled = styled.format("{:,.2f} €", subset=(row, numeric_cols))

        elif "€" in str(metric):
            styled = styled.format("{:,.0f} €", subset=(row, numeric_cols))

    # ✅ STYLE
    styled = styled \
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

        try:
            v = float(
                str(val)
                .replace(",", "")
                .replace("pp", "")
                .replace("%", "")
            )
        except:
            v = 0

        if v > 0:
            styles.append("background-color: #e6ffed;")
        elif v < 0:
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

    if customer:
        d0 = df[df["customer"].isin(customer)]
    else:
        d0 = df.copy()

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
                
        st.subheader("🟢 Unit Table (€/unit view)")
        st.caption("Values normalized per unit (€/unit). Derived from total values divided by units to show efficiency and margin structure.")

        unit_table = build_unit_table(df_group, scenarios)
        show_table(unit_table)
        st.download_button(
            label="⬇️ Download Unit Excel",
            data=to_excel(unit_table),
            file_name=f"unit_table_{level_name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # ===============================
        # TOTAL TABLE
        # ===============================
        
        st.subheader("🔵 Total (absolute € view)")
        st.caption("Aggregated values directly from source data (after filtering and grouping). Represents total financial results in absolute €.")

        total_table = build_total_table(df_group, scenarios)
        show_table(total_table)
        st.download_button(
            label="⬇️ Download Total Excel",
            data=to_excel(total_table),
            file_name=f"total_table_{level_name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.divider()


# ==================================================
if __name__ == "__main__":
    render()