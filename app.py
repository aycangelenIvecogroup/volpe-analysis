import streamlit as st

from ui.sidebar import render_sidebar
from views.overview import render_overview
from views.customer_detail import render_customer_detail
from views.deep_dive import render_deep_dive
from views.problems import render_problems

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

if page == "Overview":
    render_overview(controls)

elif page == "Customer Detail":
    render_customer_detail(controls)

elif page == "Problems":
    render_problems()

elif page == "Deep Dive":
    render_deep_dive(controls)
