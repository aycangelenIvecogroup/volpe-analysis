import streamlit as st


def render_sidebar():
    st.sidebar.title("🎛️ Control Panel")

    # ----------------------------
    # NAVIGATION
    # ----------------------------
    page = st.sidebar.radio(
    "Navigation",
    ["Overview", "Customer Detail", "Deep Dive", "Advanced Analysis", "Problems"]
)
    st.sidebar.markdown("---")

    # ----------------------------
    # SCENARIO
    # ----------------------------
    scenario = st.sidebar.selectbox(
        "Scenario",
        ["ACT", "AGM25", "B26", "FCST26"]
    )

    st.sidebar.markdown("---")

    # ----------------------------
    # TIME
    # ----------------------------
    month = st.sidebar.selectbox(
        "Month",
        ["March", "February"]
    )

    st.sidebar.markdown("---")

    # ----------------------------
    # RANKING
    # ----------------------------
    st.sidebar.markdown("### Ranking Focus")

    rank_mode = st.sidebar.radio(
        "Rank customers by",
        [
            "Sales Execution (Coverage)",
            "Margin Deviation (AGM Gap)"
        ]
    )

    st.sidebar.markdown("---")

    # ----------------------------
    # RISK
    # ----------------------------
    st.sidebar.markdown("### Risk Definition (Coverage %)")

    critical_below = st.sidebar.number_input(
        "CRITICAL if coverage below",
        min_value=0,
        max_value=100,
        value=70,
        step=1
    )

    warning_below = st.sidebar.number_input(
        "WARNING if coverage below",
        min_value=critical_below + 1,
        max_value=100,
        value=90,
        step=1
    )

    
    controls = {
        "scenario": scenario,
        "month": month,
        "rank_mode": rank_mode,
        "critical_below": critical_below,
        "warning_below": warning_below,
    }

    return page, controls
