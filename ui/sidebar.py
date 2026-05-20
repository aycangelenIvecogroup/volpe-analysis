import streamlit as st
st.markdown("""
<style>

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #ffe4e6, #fbcfe8);
}


div[role="radiogroup"] > label {
    padding: 8px 12px;
    margin: 4px 0;
    border-radius: 10px;
    transition: all 0.2s ease;
}

div[role="radiogroup"] > label:hover {
    background-color: #e0e7ff;
    cursor: pointer;
}

div[role="radiogroup"] label[data-checked="true"] {
    background-color: #6366f1 !important;
    color: white !important;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)
def render_sidebar():
    with st.sidebar:

        st.markdown(
            "<h2 style='text-align: center;'>🎛️ Control Panel 😺</h2>",
            unsafe_allow_html=True
        )

        st.markdown("---")

        page = st.radio(
            "",
            [
                "🏠 Dashboard",
                "👥 Customer Analysis",
                "💡 Insights",
                "📦 Product Analysis",
                "⚖️ Comparison",
                "📊 Unit Bridge",
                "⚠️ Problems",
            ]
        )

        st.markdown("---")

        st.markdown(
            "<p style='text-align:center; font-size:12px; color:gray;'>Made by ❤️ Aycan Gelen</p>",
            unsafe_allow_html=True
        )

    return page