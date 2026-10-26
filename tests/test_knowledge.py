"""Tests for knowledge loading and keyword retrieval."""

import tempfile
import unittest
from pathlib import Path

from services.knowledge_service import (
    add_knowledge,
    load_knowledge,
    normalize_text,
    search_knowledge,
)
from services.storage_service import PROJECT_ROOT


KNOWLEDGE_FILE = PROJECT_ROOT / "data" / "knowledge_base.json"

ORIGINAL_RECORDS = {
    "KB-001": {
        "category": "Income",
        "question": "What is net pay?",
        "answer": "Net pay is the amount of earnings remaining after applicable deductions.",
        "keywords": ["net pay", "take home pay", "salary after deductions"],
        "source": "Instructor-approved glossary",
    },
    "KB-002": {
        "category": "Income",
        "question": "What is gross pay?",
        "answer": "Gross pay is the total amount earned before deductions.",
        "keywords": ["gross pay", "salary before deductions", "gross salary"],
        "source": "Instructor-approved glossary",
    },
    "KB-003": {
        "category": "Budgeting",
        "question": "What is a budget?",
        "answer": "A budget is a plan for managing income and expenses over a period of time.",
        "keywords": ["budget", "financial plan", "monthly budget"],
        "source": "Instructor-approved glossary",
    },
    "KB-004": {
        "category": "Budgeting",
        "question": "What is a budget balance?",
        "answer": (
            "A budget balance is the amount remaining after recorded expenses "
            "are subtracted from the income allocated to the same period."
        ),
        "keywords": ["budget balance", "remaining money", "income minus expenses"],
        "source": "Instructor-approved glossary",
    },
    "KB-005": {
        "category": "Expenses",
        "question": "What are utility expenses?",
        "answer": "Utility expenses commonly include household services such as electricity and water.",
        "keywords": ["utilities", "electricity", "water", "utility bills"],
        "source": "Instructor-approved glossary",
    },
    "KB-006": {
        "category": "Expenses",
        "question": "What is a recurring expense?",
        "answer": (
            "A recurring expense is a cost that occurs repeatedly, such as "
            "monthly rent or an internet subscription."
        ),
        "keywords": ["recurring expense", "monthly bills", "regular payments"],
        "source": "Instructor-approved glossary",
    },
}


class KnowledgeServiceTests(unittest.TestCase):
    def test_normalize_text_removes_punctuation_and_case(self):
        self.assertEqual(
            normalize_text("  What is Net Pay? "),
            "what is net pay",
        )

    def test_original_records_load_unchanged(self):
        records = load_knowledge()
        by_id = {record["id"]: record for record in records}
        for record_id, expected in ORIGINAL_RECORDS.items():
            self.assertEqual(by_id[record_id]["category"], expected["category"])
            self.assertEqual(by_id[record_id]["question"], expected["question"])
            self.assertEqual(by_id[record_id]["answer"], expected["answer"])
            self.assertEqual(by_id[record_id]["keywords"], expected["keywords"])
            self.assertEqual(by_id[record_id]["source"], expected["source"])

    def test_five_supplementary_records_are_pending_review(self):
        records = load_knowledge()
        supplementary = [
            record
            for record in records
            if record["source"] == "Supplementary example — pending instructor review"
        ]
        self.assertGreaterEqual(len(supplementary), 5)
        for record in supplementary:
            self.assertTrue(record["id"])
            self.assertTrue(record["category"].strip())
            self.assertTrue(record["question"].strip())
            self.assertTrue(record["answer"].strip())
            self.assertGreaterEqual(len(record["keywords"]), 1)
            self.assertNotEqual(record["source"], "Instructor-approved glossary")

    def test_add_knowledge_persists_a_valid_record(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "knowledge_base.json"
            created = add_knowledge(
                "Savings",
                "What is a sinking fund?",
                "A sinking fund is money set aside for a planned future cost.",
                "sinking fund, planned savings",
                "Class example",
                path,
            )
            self.assertTrue(created["id"].startswith("KB-"))
            self.assertEqual(
                created["keywords"],
                ["sinking fund", "planned savings"],
            )
            loaded = load_knowledge(path)
            self.assertEqual(loaded[0]["question"], "What is a sinking fund?")

    def test_add_knowledge_rejects_incomplete_records(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "knowledge_base.json"
            with self.assertRaises(ValueError):
                add_knowledge(" ", "Question", "Answer", "keyword", "Source", path)
            with self.assertRaises(ValueError):
                add_knowledge("Category", "Question", "Answer", " , ", "Source", path)
            self.assertFalse(path.exists())

    def test_exact_question_ranks_net_pay_first(self):
        results = search_knowledge("What is net pay?")
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]["record"]["id"], "KB-001")

    def test_keyword_synonym_ranks_net_pay_first(self):
        results = search_knowledge("take home pay")
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]["record"]["id"], "KB-001")

    def test_stop_words_do_not_match_on_their_own(self):
        self.assertEqual(search_knowledge("What is the"), [])
        self.assertEqual(search_knowledge("what is my a an"), [])

    def test_unrelated_compound_interest_question_has_no_match(self):
        results = search_knowledge("How do I calculate compound interest?")
        self.assertEqual(results, [])

    def test_search_reads_an_isolated_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "knowledge_base.json"
            add_knowledge(
                "Income",
                "What is net pay?",
                "Net pay is take-home earnings.",
                "net pay, take home pay",
                "Test fixture",
                path,
            )
            results = search_knowledge("take home pay", path)
            self.assertEqual(results[0]["record"]["source"], "Test fixture")
            self.assertFalse(
                any(
                    item["record"]["id"] == "KB-002"
                    for item in results
                )
            )


if __name__ == "__main__":
    unittest.main()
