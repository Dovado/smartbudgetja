"""Tests for JSON loading and atomic saving."""

import json
import tempfile
import unittest
from pathlib import Path

from services.storage_service import load_finances, load_json, save_finances, save_json


class StorageServiceTests(unittest.TestCase):
    def test_save_and_load_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "finances.json"
            payload = {
                "income_cents": 0,
                "monthly_income": {"2026-10": 18_000_000},
                "expenses": [
                    {
                        "id": "EXP-001",
                        "provider": "JPS",
                        "category": "Utilities",
                        "amount_cents": 1_500_000,
                        "month": "2026-10",
                    }
                ],
            }
            save_finances(payload, path)
            loaded = load_finances(path)
            self.assertEqual(loaded["monthly_income"]["2026-10"], 18_000_000)
            self.assertEqual(loaded["expenses"][0]["provider"], "JPS")
            self.assertEqual(path.read_text(encoding="utf-8")[:1], "{")

    def test_missing_file_returns_default_without_creating_it(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.json"
            loaded = load_json(path, {"income_cents": 0, "expenses": []})
            self.assertEqual(loaded, {"income_cents": 0, "expenses": []})
            self.assertFalse(path.exists())

            finances = load_finances(path)
            self.assertEqual(finances["income_cents"], 0)
            self.assertEqual(finances["monthly_income"], {})
            self.assertEqual(finances["expenses"], [])
            self.assertFalse(path.exists())

    def test_malformed_json_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.json"
            path.write_text("{not json", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_json(path, {"fallback": True})
            self.assertEqual(path.read_text(encoding="utf-8"), "{not json")
            with self.assertRaises(ValueError):
                load_finances(path)
            self.assertEqual(path.read_text(encoding="utf-8"), "{not json")

    def test_repeated_saves_preserve_records(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "finances.json"
            save_json(path, {"income_cents": 10, "expenses": []})
            save_json(
                path,
                {
                    "income_cents": 10,
                    "monthly_income": {"2026-10": 20},
                    "expenses": [{"id": "1", "amount_cents": 5}],
                },
            )
            loaded = load_finances(path)
            self.assertEqual(loaded["income_cents"], 10)
            self.assertEqual(len(loaded["expenses"]), 1)
            self.assertEqual(loaded["monthly_income"]["2026-10"], 20)

    def test_legacy_income_is_not_assigned_or_rewritten_on_load(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "finances.json"
            original = {
                "income_cents": 18_000_000,
                "expenses": [],
            }
            path.write_text(json.dumps(original), encoding="utf-8")
            loaded = load_finances(path)
            self.assertEqual(loaded["income_cents"], 18_000_000)
            self.assertEqual(loaded["monthly_income"], {})
            on_disk = json.loads(path.read_text(encoding="utf-8"))
            self.assertNotIn("monthly_income", on_disk)
            self.assertEqual(on_disk["income_cents"], 18_000_000)

    def test_atomic_save_leaves_no_temporary_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.json"
            save_json(path, {"ok": True})
            leftovers = list(Path(directory).glob("*.tmp"))
            self.assertEqual(leftovers, [])
            self.assertEqual(load_json(path, {}), {"ok": True})

    def test_failed_save_keeps_the_original_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.json"
            save_json(path, {"kept": True})

            class NotSerializable:
                pass

            with self.assertRaises(TypeError):
                save_json(path, {"bad": NotSerializable()})
            self.assertEqual(load_json(path, {}), {"kept": True})
            self.assertEqual(list(Path(directory).glob("*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
