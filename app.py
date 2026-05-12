import streamlit as st

from ui.sidebar import render_sidebar
from views.customer_analysis import render_customer_analysis
from views.problems import render_problems
from views.advanced_analysis import render_advanced_analysis
from views.comparison import render_comparison
from views.unit_bridge import render_unit_bridge
from views.insights import render_full_diagnostic
from views.product_analysis import render_product_analysis



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

page, controls = render_sidebar()

# ==================================================
# PAGE ROUTING
# ==================================================

if page == "Customer Analysis":
    render_customer_analysis(controls)


elif page == "Problems":
    render_problems()
    
elif page == "Advanced Analysis":
    render_advanced_analysis()

elif page == "Comparison":
    render_comparison()


elif page == "Unit Bridge":
    render_unit_bridge()
elif page == "Product Analysis":
    render_product_analysis()
elif page == "insights":
    render_full_diagnostic()

