import streamlit as st

def render_sidebar():

    if "page" not in st.session_state:
        st.session_state.page = "📊 Customer Overview"

    with st.sidebar:

        st.markdown("## Control Panel")

        def menu_item(label, desc):
            active = st.session_state.page == label

            bg = "#4f46e5" if active else "transparent"
            color = "white" if active else "#374151"

            if st.markdown(
                f"""
                <div style="
                    padding:10px;
                    border-radius:8px;
                    background:{bg};
                    color:{color};
                    margin-bottom:6px;
                ">
                    <div style="font-weight:600;">{label}</div>
                    <div style="font-size:11px; opacity:0.7;">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True
            ):
                st.session_state.page = label

        # menu
        if st.button("📊 Customer Overview"):
            st.session_state.page = "📊 Customer Overview"

        st.caption("Customer performance summary")

        if st.button("🧪 Scenario Builder"):
            st.session_state.page = "🧪 Scenario Builder"

        st.caption("Simulate pricing & volume")

        if st.button("📊 Unit Bridge"):
            st.session_state.page = "📊 Unit Bridge"

        st.caption("Analyze margin drivers")

        st.markdown("---")
        st.caption("Aycan Gelen")

    return st.session_state.page
