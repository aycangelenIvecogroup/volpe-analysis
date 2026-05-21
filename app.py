import streamlit as st
import os

from ui.sidebar import render_sidebar
from views.customer_analysis import render_customer_analysis
from views.problems import render_problems
from views.comparison import render_comparison
from views.unit_bridge import render_unit_bridge
from views.insights import render_full_diagnostic
from views.product_analysis import render_product_analysis
from views.dashboard import render_dashboard
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

# =========================
# 🔧 CONFIG
# =========================
st.set_page_config(
    page_title="Volpe Analytics Platform",
    layout="wide"
)

# =========================
# 🔐 SESSION
# =========================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# =========================
# 🔐 LOGIN
# =========================
if not st.session_state["authenticated"]:

    # LOGO (center)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("logo.jpg", width=200)

    # ✅ SADE TEXT
    st.markdown("<h1 style='text-align:center; color:#ef233c;'>Volpe Analytics</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:gray;'>Secure Access Platform</p>", unsafe_allow_html=True)

    st.markdown("---")

    # PASSWORD
    password = st.text_input("Enter password", type="password")

    PASSWORD = os.getenv("APP_PASSWORD") or st.secrets.get("APP_PASSWORD")

    if password:
        if password == PASSWORD:
            st.success("Access granted ✅")
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Invalid password")

    st.markdown("---")
    st.caption("🔒 Internal tool – authorized access only")
    st.caption("Made by ❤️ Aycan Gelen")

    st.stop()

# =========================
# 📊 APP
# =========================
selected = render_sidebar()

pages = {
    "🏠 Dashboard": render_dashboard,
    "👥 Customer Analysis": render_customer_analysis,
    "💡 Insights": render_full_diagnostic,
    "📦 Product Analysis": render_product_analysis,
    "⚖️ Comparison": render_comparison,
    "📊 Unit Bridge": render_unit_bridge,
    "⚠️ Problems": render_problems,
}

pages[selected]()