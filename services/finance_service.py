"""Monetary conversion and budget calculations.

Amounts are stored as integer Jamaican cents so totals do not depend on
binary floating-point arithmetic.
"""

import re
from decimal import Decimal, InvalidOperation


MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

EXPENSE_CATEGORIES = [
    "Utilities",
    "Telecommunications",
    "Housing",
    "Groceries",
    "Transportation",
    "Credit Card",
    "Other",
]


def to_cents(amount):
    """Convert a Jamaican dollar amount into integer cents."""
    try:
        value = Decimal(str(amount))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("Invalid monetary amount.") from None

    if not value.is_finite():
        raise ValueError("Amount must be finite.")
    if value < 0:
        raise ValueError("Amount cannot be negative.")
    # exponent < -2 means more than two digits after the decimal point.
    if value.as_tuple().exponent < -2:
        raise ValueError("Use no more than two decimal places.")
    return int(value * 100)


def format_money(cents):
    """Format integer cents as Jamaican dollars, such as J$15,000.00."""
    cents = int(cents)
    sign = "-" if cents < 0 else ""
    dollars, remainder = divmod(abs(cents), 100)
    return f"{sign}J${dollars:,}.{remainder:02d}"


def calculate_total_expenses(expenses):
    """Return the sum of amount_cents for the given expense records."""
    return sum(expense["amount_cents"] for expense in expenses)


def calculate_balance(income_cents, expenses):
    """Return income minus total expenses, in integer cents."""
    return income_cents - calculate_total_expenses(expenses)


def is_valid_month(month):
    """Return True when month is a YYYY-MM string."""
    return isinstance(month, str) and MONTH_PATTERN.fullmatch(month) is not None


def month_options(start_year=2025, end_year=2027):
    """Return YYYY-MM labels for the month selector."""
    return [
        f"{year}-{month:02d}"
        for year in range(start_year, end_year + 1)
        for month in range(1, 13)
    ]


def filter_expenses_by_month(expenses, month):
    """Keep only expenses recorded for the selected month."""
    return [
        expense
        for expense in expenses
        if expense.get("month") == month
    ]


def calculate_monthly_expenses(expenses, month):
    """Sum expenses that belong to one month."""
    return calculate_total_expenses(
        filter_expenses_by_month(expenses, month)
    )


def calculate_monthly_balance(income_cents, expenses, month):
    """Return one month's income minus that month's expenses."""
    return calculate_balance(
        income_cents,
        filter_expenses_by_month(expenses, month),
    )


def get_month_income(data, month):
    """Return saved income for a month.

    Legacy files may contain income_cents with no month. That value is not
    treated as income for any particular month until the user assigns it.
    """
    monthly_income = data.get("monthly_income") or {}
    return int(monthly_income.get(month, 0))


def demonstration_finances():
    """Return the fictional October 2026 records from the lesson.

    This function does not write to disk.
    """
    samples = [
        ("demo-jps", "JPS", "Utilities", "15000"),
        ("demo-nwc", "NWC", "Utilities", "5000"),
        ("demo-flow", "Flow", "Telecommunications", "7500"),
        ("demo-groceries", "Groceries", "Groceries", "25000"),
        ("demo-rent", "Rent", "Housing", "45000"),
        ("demo-transport", "Transport", "Transportation", "15000"),
    ]
    return {
        "income_cents": 0,
        "monthly_income": {
            "2026-10": to_cents("180000"),
        },
        "expenses": [
            {
                "id": expense_id,
                "provider": provider,
                "category": category,
                "amount_cents": to_cents(amount),
                "month": "2026-10",
            }
            for expense_id, provider, category, amount in samples
        ],
    }
