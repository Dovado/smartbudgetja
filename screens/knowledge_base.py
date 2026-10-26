"""Knowledge base screen."""

import streamlit as st

from services.knowledge_service import add_knowledge, load_knowledge


def show_knowledge_base():
    """List stored knowledge and accept a new record."""
    st.title("SmartBudget Knowledge Base")
    st.write("Explore and manage financial knowledge.")

    notice = st.session_state.pop("knowledge_notice", None)
    if notice:
        st.success(notice)

    try:
        records = load_knowledge()
    except ValueError as error:
        st.error(str(error))
        return

    st.metric("Knowledge Records", len(records))
    st.divider()
    st.subheader("Available Knowledge")
    if not records:
        st.info("No knowledge records available.")

    for record in records:
        with st.expander(record["question"]):
            st.write(record["answer"])
            st.caption(f"Category: {record['category']}")
            keywords = ", ".join(record.get("keywords", []))
            st.caption(f"Keywords: {keywords}")
            st.caption(f"Source: {record['source']}")

    st.divider()
    st.subheader("Add Knowledge")
    with st.form("knowledge_form"):
        category = st.text_input("Category")
        question = st.text_input("Question")
        answer = st.text_area("Answer")
        keywords = st.text_input("Keywords (comma separated)")
        source = st.text_input("Information Source")
        submitted = st.form_submit_button("Save Knowledge")

    if submitted:
        try:
            add_knowledge(
                category,
                question,
                answer,
                keywords,
                source,
            )
        except ValueError as error:
            st.error(str(error))
        else:
            st.session_state.knowledge_notice = "Knowledge record saved."
            st.rerun()
