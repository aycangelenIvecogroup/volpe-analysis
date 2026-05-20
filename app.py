import streamlit as st

from ui.sidebar import render_sidebar
from views.customer_analysis import render_customer_analysis
from views.problems import render_problems

from views.comparison import render_comparison
from views.unit_bridge import render_unit_bridge
from views.insights import render_full_diagnostic
from views.product_analysis import render_product_analysis
from views.dashboard import render_dashboard



# ==================================================
# PAGE CONFIG
# ==================================================

st.set_page_config(
    page_title="Volpe Sales Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================================================
# SIDEBAR (ROUTER + CONTROLS)
# ==================================================


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



