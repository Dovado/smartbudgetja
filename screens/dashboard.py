"""Dashboard screen."""

import streamlit as st

from services.finance_service import (
    calculate_monthly_balance,
    calculate_monthly_expenses,
    filter_expenses_by_month,
    format_money,
    get_month_income,
    month_options,
)


def show_dashboard():
    """Render the monthly overview and category chart."""
    st.title("SmartBudget JA Dashboard")
    st.write("Your personal financial overview.")

    data = st.session_state.finances
    data.setdefault("monthly_income", {})
    data.setdefault("expenses", [])

    options = month_options()
    current = st.session_state.selected_month
    if current not in options:
        options = [current, *options]
    st.selectbox("Month", options, key="selected_month")
    month = st.session_state.selected_month

    income = get_month_income(data, month)
    expenses = filter_expenses_by_month(data["expenses"], month)
    total_expenses = calculate_monthly_expenses(data["expenses"], month)
    balance = calculate_monthly_balance(income, data["expenses"], month)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Monthly Net Income", format_money(income))
    with col2:
        st.metric("Recorded Expenses", format_money(total_expenses))
    with col3:
        st.metric("Estimated Balance", format_money(balance))

    st.divider()
    if expenses:
        st.subheader("Expenses by Category")
        category_totals = {}
        for expense in expenses:
            category = expense["category"]
            category_totals[category] = (
                category_totals.get(category, 0)
                + expense["amount_cents"]
            )
        st.bar_chart(
            {
                "Category": list(category_totals.keys()),
                "Amount (J$)": [
                    cents / 100
                    for cents in category_totals.values()
                ],
            },
            x="Category",
            y="Amount (J$)",
        )
        st.caption(f"Category totals for {month}, in Jamaican dollars.")
    else:
        st.info("Add expenses to see your dashboard.")
