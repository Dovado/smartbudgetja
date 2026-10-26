"""JSON persistence for SmartBudget JA.

Files are replaced atomically so a failed save does not leave a partial file.
"""

import json
import os
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
FINANCE_FILE = DATA_DIR / "finances.json"
DOCUMENTS_FILE = DATA_DIR / "documents.json"

DEFAULT_FINANCES = {
    "income_cents": 0,
    "monthly_income": {},
    "expenses": [],
}


def load_json(file_path, default):
    """Load JSON, or return default when the file is missing.

    Malformed JSON raises ValueError and does not modify the file.
    """
    path = Path(file_path)
    if not path.exists():
        return default

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Could not read {path.name} because the JSON is invalid. "
            "The saved file was not changed."
        ) from error


def save_json(file_path, data):
    """Write JSON via a temporary file, then replace the destination."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        # Close the temp file before replacing it. Windows cannot rename a
        # file that is still open.
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            suffix=".tmp",
            delete=False,
        ) as file:
            temporary_path = file.name
            json.dump(data, file, indent=4, ensure_ascii=False)
            file.write("\n")
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.remove(temporary_path)


def ensure_finance_shape(data):
    """Normalize financial data without assigning legacy income to a month."""
    if not isinstance(data, dict):
        raise ValueError(
            "Financial data must be a JSON object. The saved file was not changed."
        )

    monthly_income = data.get("monthly_income") or {}
    if not isinstance(monthly_income, dict):
        raise ValueError(
            "monthly_income must be a JSON object. The saved file was not changed."
        )

    expenses = data.get("expenses") or []
    if not isinstance(expenses, list):
        raise ValueError(
            "expenses must be a JSON array. The saved file was not changed."
        )

    return {
        "income_cents": int(data.get("income_cents", 0)),
        "monthly_income": {
            str(month): int(amount)
            for month, amount in monthly_income.items()
        },
        "expenses": list(expenses),
    }


def load_finances(file_path=None):
    """Load finances from disk.

    A missing file returns the default structure and is not created here.
    A legacy file that only has income_cents keeps that value unassigned.
    """
    path = Path(file_path) if file_path else FINANCE_FILE
    # Use the original lesson shape as the missing-file default. The month
    # map is added in memory and is not written back during loading.
    data = load_json(
        path,
        {
            "income_cents": 0,
            "expenses": [],
        },
    )
    return ensure_finance_shape(data)


def save_finances(data, file_path=None):
    """Save the financial document."""
    path = Path(file_path) if file_path else FINANCE_FILE
    save_json(path, data)
