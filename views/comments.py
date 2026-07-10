import pandas as pd
import streamlit as st

from services.comments_db import (
    get_all_comments
)


def render():

    st.title("💬 Team Comments")

    comments = get_all_comments()

    if not comments:
        st.info("No comments found")
        return

    df = pd.DataFrame(
        comments,
        columns=[
            "customer",
            "user",
            "created_at",
            "comment"
        ]
    )
    col1, col2, col3 = st.columns(3)

    with col1:

        selected_customer = st.selectbox(
            "Customer",
            ["All"]
            + sorted(df["customer"].unique().tolist())
        )

    with col2:

        selected_user = st.selectbox(
            "User",
            ["All"]
            + sorted(df["user"].unique().tolist())
        )

    with col3:

        search_text = st.text_input(
            "Search"
        )
    filtered = df.copy()

    if selected_customer != "All":

        filtered = filtered[
            filtered["customer"]
            == selected_customer
        ]

    if selected_user != "All":

        filtered = filtered[
            filtered["user"]
            == selected_user
        ]

    if search_text:

        filtered = filtered[
            filtered["comment"]
            .str.contains(
                search_text,
                case=False,
                na=False
            )
        ]
    st.write(
        f"Showing {len(filtered)} comments"
    )

    for _, row in filtered.iterrows():

        st.markdown(
            f"""
    ### {row['customer']}

    **{row['user']}** | {row['created_at']}

    {row['comment']}
    """
        )

        st.divider()