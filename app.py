"""SmartBudget JA application entry point."""

import streamlit as st

from screens.ask_smartbudget import show_ask_smartbudget
from screens.dashboard import show_dashboard
from screens.documents import show_documents
from screens.finances import show_finances
from screens.knowledge_base import show_knowledge_base
from services.storage_service import load_finances


st.set_page_config(
    page_title="SmartBudget JA",
    layout="wide",
)

if "finances" not in st.session_state:
    try:
        st.session_state.finances = load_finances()
    except ValueError as error:
        st.session_state.finance_load_error = str(error)
    else:
        st.session_state.pop("finance_load_error", None)

if "selected_month" not in st.session_state:
    st.session_state.selected_month = "2026-10"

# Apply a month change requested by a screen after its widgets were drawn.
if "pending_month" in st.session_state:
    st.session_state.selected_month = st.session_state.pop("pending_month")

st.sidebar.title("SmartBudget JA")
st.sidebar.caption("Personal Financial Management")
st.sidebar.divider()
menu = st.sidebar.radio(
    "Main Menu",
    [
        "Dashboard",
        "Income & Expenses",
        "Documents",
        "Knowledge Base",
        "Ask SmartBudget",
    ],
    key="main_menu",
)

finance_error = st.session_state.get("finance_load_error")
if finance_error and menu in {"Dashboard", "Income & Expenses"}:
    st.error(finance_error)
elif menu == "Dashboard":
    show_dashboard()
elif menu == "Income & Expenses":
    show_finances()
elif menu == "Documents":
    show_documents()
elif menu == "Knowledge Base":
    show_knowledge_base()
elif menu == "Ask SmartBudget":
    show_ask_smartbudget()

st.divider()
st.caption("Amber National AI Lab | SmartBudget JA Learning Project")
