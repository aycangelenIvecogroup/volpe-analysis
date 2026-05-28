import streamlit as st
import os

from views.unit_bridge import render as render_unit_bridge
from views.customer_overview import render_customer_overview 
from views.scenario_builder import render_scenario_builder
from ui.sidebar import render_sidebar

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

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("logo.jpg", width=200)

    st.markdown(
        "<h1 style='text-align:center; color:#ef233c;'>Volpe Analytics</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='text-align:center; color:gray;'>Secure Access Platform</p>",
        unsafe_allow_html=True
    )

    st.markdown("---")

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
# 📊 PAGES
# =========================
pages = {
    "📊 Customer Overview": render_customer_overview,
    "🧪 Scenario Builder": render_scenario_builder,
    "📊 Unit Bridge": render_unit_bridge,
}

selected_page = render_sidebar()

func = pages.get(selected_page)

if func:
    func()
