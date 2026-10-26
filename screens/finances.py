"""Income and expense screen."""

import uuid

import streamlit as st

from services.finance_service import (
    EXPENSE_CATEGORIES,
    calculate_monthly_balance,
    calculate_monthly_expenses,
    demonstration_finances,
    filter_expenses_by_month,
    format_money,
    get_month_income,
    is_valid_month,
    month_options,
    to_cents,
)
from services.storage_service import save_finances


def _month_choices():
    options = month_options()
    current = st.session_state.selected_month
    if current not in options:
        options = [current, *options]
    return options


def _show_flash():
    notice = st.session_state.pop("finance_notice", None)
    if notice:
        st.success(notice)


def show_finances():
    """Render income entry, expenses, and the monthly summary."""
    st.title("Income & Expenses")
    st.write("Manage your monthly income and expenses.")
    _show_flash()

    data = st.session_state.finances
    data.setdefault("monthly_income", {})
    data.setdefault("expenses", [])
    data.setdefault("income_cents", 0)

    st.selectbox(
        "Selected month",
        _month_choices(),
        key="selected_month",
    )
    month = st.session_state.selected_month

    with st.container(border=True):
        st.subheader("Monthly Income")
        st.caption(f"Income saved for {month}")
        legacy_income = int(data.get("income_cents") or 0)
        if legacy_income > 0 and month not in data["monthly_income"]:
            st.info(
                f"Saved income of {format_money(legacy_income)} "
                "is not assigned to a month."
            )
            if st.button(
                "Assign unassigned income to this month",
                key="assign_legacy_income",
            ):
                data["monthly_income"][month] = legacy_income
                save_finances(data)
                st.session_state.refresh_salary = True
                st.session_state.finance_notice = (
                    f"Income assigned to {month}."
                )
                st.rerun()

        salary_key = f"salary_input_{month}"
        if (
            st.session_state.pop("refresh_salary", False)
            or salary_key not in st.session_state
        ):
            saved_dollars = get_month_income(data, month) / 100
            st.session_state[salary_key] = float(f"{saved_dollars:.2f}")
        income = st.number_input(
            "Net Monthly Salary (J$)",
            min_value=0.0,
            step=1000.0,
            format="%.2f",
            key=salary_key,
        )
        if st.button("Save Income", key="save_income"):
            try:
                data["monthly_income"][month] = to_cents(
                    f"{income:.2f}"
                )
            except ValueError as error:
                st.error(str(error))
            else:
                save_finances(data)
                st.session_state.finance_notice = (
                    f"Income saved for {month}."
                )
                st.rerun()

    expense_month_key = f"expense_month_{month}"
    if expense_month_key not in st.session_state:
        st.session_state[expense_month_key] = month

    with st.container(border=True):
        st.subheader("Add Expense")
        with st.form("expense_form"):
            provider = st.text_input("Provider / Description")
            category = st.selectbox("Category", EXPENSE_CATEGORIES)
            amount = st.number_input(
                "Amount (J$)",
                min_value=0.0,
                step=100.0,
                format="%.2f",
            )
            expense_month = st.text_input(
                "Month (YYYY-MM)",
                key=expense_month_key,
            )
            submitted = st.form_submit_button("Add Expense")

        if submitted:
            if not provider.strip():
                st.error("Enter a provider or description.")
            elif not is_valid_month(expense_month):
                st.error("Use a valid YYYY-MM month.")
            elif amount <= 0:
                st.error("Amount must be greater than zero.")
            else:
                try:
                    amount_cents = to_cents(f"{amount:.2f}")
                except ValueError as error:
                    st.error(str(error))
                else:
                    data["expenses"].append({
                        "id": str(uuid.uuid4()),
                        "provider": provider.strip(),
                        "category": category,
                        "amount_cents": amount_cents,
                        "month": expense_month,
                    })
                    save_finances(data)
                    if expense_month != month:
                        st.session_state.pending_month = expense_month
                    st.session_state.finance_notice = "Expense saved."
                    st.rerun()

    st.subheader("Recorded Expenses")
    month_expenses = filter_expenses_by_month(data["expenses"], month)
    if month_expenses:
        for expense in month_expenses:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{expense['provider']}**")
                    st.caption(
                        f"{expense['category']} | {expense['month']}"
                    )
                with col2:
                    st.write(format_money(expense["amount_cents"]))
                    if st.button(
                        "Delete",
                        key=f"delete_{expense['id']}",
                    ):
                        data["expenses"] = [
                            item
                            for item in data["expenses"]
                            if item["id"] != expense["id"]
                        ]
                        save_finances(data)
                        st.session_state.finance_notice = "Expense deleted."
                        st.rerun()
    else:
        st.info(f"No expenses recorded for {month}.")

    st.divider()
    income_cents = get_month_income(data, month)
    total = calculate_monthly_expenses(data["expenses"], month)
    balance = calculate_monthly_balance(
        income_cents,
        data["expenses"],
        month,
    )
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Net Income", format_money(income_cents))
    with col2:
        st.metric("Expenses", format_money(total))
    with col3:
        st.metric("Remaining", format_money(balance))
    if balance < 0:
        st.warning("Expenses exceed income for this month.")

    with st.expander("Demonstration data"):
        st.write(
            "Load the fictional October 2026 records: "
            "income J$180,000.00 and six household expenses."
        )
        confirm = st.checkbox(
            "Replace current records with the October 2026 demonstration data",
            key="confirm_demo_data",
        )
        if st.button("Load demonstration data", key="load_demo_data"):
            if not confirm:
                st.error(
                    "Confirm that the current records can be replaced."
                )
            else:
                st.session_state.finances = demonstration_finances()
                save_finances(st.session_state.finances)
                st.session_state.pending_month = "2026-10"
                st.session_state.refresh_salary = True
                st.session_state.finance_notice = (
                    "October 2026 demonstration data loaded."
                )
                st.rerun()
