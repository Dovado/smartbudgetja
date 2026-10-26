"""Tests for monetary conversion and monthly calculations."""

import unittest
from decimal import Decimal

from services.finance_service import (
    calculate_balance,
    calculate_monthly_balance,
    calculate_monthly_expenses,
    calculate_total_expenses,
    demonstration_finances,
    filter_expenses_by_month,
    format_money,
    get_month_income,
    is_valid_month,
    to_cents,
)


class FinanceServiceTests(unittest.TestCase):
    def test_to_cents_converts_whole_and_fractional_amounts(self):
        self.assertEqual(to_cents("15000"), 1_500_000)
        self.assertEqual(to_cents("15000.00"), 1_500_000)
        self.assertEqual(to_cents("5000.50"), 500_050)
        self.assertEqual(to_cents(Decimal("180000")), 18_000_000)
        self.assertEqual(to_cents(0), 0)

    def test_to_cents_rejects_extra_decimal_places(self):
        with self.assertRaises(ValueError):
            to_cents("15.555")
        with self.assertRaises(ValueError):
            to_cents("1.234")

    def test_to_cents_rejects_negative_amounts(self):
        with self.assertRaises(ValueError):
            to_cents("-1")
        with self.assertRaises(ValueError):
            to_cents("-0.01")

    def test_to_cents_rejects_nonfinite_and_invalid_values(self):
        for amount in (float("nan"), float("inf"), "NaN", "Infinity", "abc", None):
            with self.assertRaises(ValueError):
                to_cents(amount)

    def test_format_money_uses_integer_cents(self):
        self.assertEqual(format_money(1_500_000), "J$15,000.00")
        self.assertEqual(format_money(500_050), "J$5,000.50")
        self.assertEqual(format_money(-250_000), "-J$2,500.00")
        self.assertEqual(format_money(0), "J$0.00")
        self.assertEqual(format_money(-50), "-J$0.50")

    def test_expense_total_and_balance(self):
        expenses = [
            {"amount_cents": to_cents("15000")},
            {"amount_cents": to_cents("5000")},
        ]
        self.assertEqual(calculate_total_expenses(expenses), 2_000_000)
        self.assertEqual(
            calculate_balance(to_cents("180000"), expenses),
            16_000_000,
        )

    def test_negative_balance_is_preserved(self):
        expenses = [{"amount_cents": to_cents("120000")}]
        balance = calculate_balance(to_cents("100000"), expenses)
        self.assertEqual(balance, -2_000_000)
        self.assertEqual(format_money(balance), "-J$20,000.00")

    def test_monthly_filter_does_not_mix_months(self):
        expenses = [
            {"amount_cents": 1_500_000, "month": "2026-10"},
            {"amount_cents": 500_000, "month": "2026-11"},
            {"amount_cents": 250_000, "month": "2026-10"},
        ]
        october = filter_expenses_by_month(expenses, "2026-10")
        self.assertEqual(len(october), 2)
        self.assertEqual(
            calculate_monthly_expenses(expenses, "2026-10"),
            1_750_000,
        )
        self.assertEqual(
            calculate_monthly_balance(10_000_000, expenses, "2026-11"),
            9_500_000,
        )
        self.assertEqual(
            calculate_monthly_expenses(expenses, "2026-12"),
            0,
        )

    def test_month_validation(self):
        self.assertTrue(is_valid_month("2026-10"))
        self.assertFalse(is_valid_month("2026-13"))
        self.assertFalse(is_valid_month("26-10"))
        self.assertFalse(is_valid_month("2026-1"))
        self.assertFalse(is_valid_month(None))

    def test_month_income_ignores_unassigned_legacy_value(self):
        data = {
            "income_cents": 18_000_000,
            "monthly_income": {"2026-11": 100_000},
            "expenses": [],
        }
        self.assertEqual(get_month_income(data, "2026-10"), 0)
        self.assertEqual(get_month_income(data, "2026-11"), 100_000)

    def test_demonstration_totals(self):
        data = demonstration_finances()
        month = "2026-10"
        income = get_month_income(data, month)
        expenses = calculate_monthly_expenses(data["expenses"], month)
        balance = calculate_monthly_balance(income, data["expenses"], month)
        self.assertEqual(income, 18_000_000)
        self.assertEqual(expenses, 11_250_000)
        self.assertEqual(balance, 6_750_000)
        self.assertEqual(format_money(income), "J$180,000.00")
        self.assertEqual(format_money(expenses), "J$112,500.00")
        self.assertEqual(format_money(balance), "J$67,500.00")
        self.assertEqual(data["income_cents"], 0)
        months = {expense["month"] for expense in data["expenses"]}
        self.assertEqual(months, {"2026-10"})


if __name__ == "__main__":
    unittest.main()
