import streamlit as st
import pandas as pd
from pathlib import Path

# ==================================================
# PATH & LOAD
# ==================================================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "customer_amount_layer_clean.xlsx"

@st.cache_data
def load_data():
    return pd.read_excel(DATA_PATH)

# ==================================================
# MAIN PAGE
# ==================================================
def render_customer_analysis(controls=None):
    df = load_data()

    st.title("📊 Customer Analysis")

    tab1, tab2, tab3 = st.tabs(["Overview", "Deep Dive", "Customer Detail"])

    # ==================================================
    # 🟢 OVERVIEW
    # ==================================================
    with tab1:
        st.subheader("Overview")

        total_tn = df["March_TN"].sum()
        total_agm = df["March_AGM"].sum()
        margin = (total_agm / total_tn * 100) if total_tn != 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Revenue", f"€ {total_tn:,.0f}")
        col2.metric("Total Margin", f"€ {total_agm:,.0f}")
        col3.metric("Margin %", f"{margin:.1f}%")

        st.dataframe(df.head(50), use_container_width=True)

    # ==================================================
    # 🔵 DEEP DIVE
    # ==================================================
    with tab2:
        st.subheader("Deep Dive")

        top_customers = (
            df.sort_values("March_TN", ascending=False)
              .head(10)[["CUSTOMER MERGE", "March_TN", "March_AGM"]]
        )

        st.write("Top 10 Customers by Revenue")
        st.dataframe(top_customers, use_container_width=True)

        st.write("Distribution")
        st.bar_chart(top_customers.set_index("CUSTOMER MERGE")["March_TN"])

    # ==================================================
    # 🟠 CUSTOMER DETAIL
    # ==================================================
    with tab3:
        st.subheader("Customer Detail")

        customers = df["CUSTOMER MERGE"].unique()
        selected_customer = st.selectbox("Select Customer", customers)

        df_cust = df[df["CUSTOMER MERGE"] == selected_customer]

        st.write("Customer Metrics")
        st.dataframe(df_cust.T, use_container_width=True)