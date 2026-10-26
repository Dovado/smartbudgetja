"""Knowledge retrieval screen."""

import streamlit as st

from services.knowledge_service import search_knowledge


def show_ask_smartbudget():
    """Retrieve a stored answer. This screen does not generate one."""
    st.title("Ask SmartBudget")
    st.write(
        "Ask a question about budgeting or financial terminology."
    )
    st.info(
        "SmartBudget retrieves an existing knowledge record. "
        "It does not generate an original explanation."
    )

    question = st.text_input(
        "Your Question",
        placeholder="What is net pay?",
        key="ask_question",
    )
    if st.button("Find Answer", key="find_answer"):
        if not question.strip():
            st.session_state.ask_warning = "Please enter a question."
            st.session_state.pop("ask_results", None)
        else:
            st.session_state.pop("ask_warning", None)
            try:
                st.session_state.ask_results = search_knowledge(question)
            except ValueError as error:
                st.session_state.ask_error = str(error)
                st.session_state.pop("ask_results", None)
            else:
                st.session_state.pop("ask_error", None)

    warning = st.session_state.get("ask_warning")
    if warning:
        st.warning(warning)
        return

    ask_error = st.session_state.get("ask_error")
    if ask_error:
        st.error(ask_error)
        return

    results = st.session_state.get("ask_results")
    if results is None:
        return

    if not results:
        st.info("No matching knowledge was found.")
        return

    best_match = results[0]
    record = best_match["record"]
    st.subheader("Best Matching Answer")
    st.write(record["answer"])
    st.caption(f"Source: {record['source']}")
    st.caption(f"Category: {record['category']}")

    if len(results) > 1:
        st.subheader("Other Possible Matches")
        for item in results[1:4]:
            other = item["record"]
            with st.expander(other["question"]):
                st.write(other["answer"])
                st.caption(f"Source: {other['source']}")
                st.caption(f"Category: {other['category']}")
