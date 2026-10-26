"""Tests for document validation, extraction, and the category index."""

import tempfile
import unittest
from pathlib import Path

import pymupdf

from services.document_service import (
    MAX_FILE_SIZE,
    add_document_record,
    extract_document_text,
    load_document_index,
    save_uploaded_file,
    validate_file,
)
from services.storage_service import PROJECT_ROOT


SAMPLE_TXT = PROJECT_ROOT / "sample_documents" / "sample_budget_faq.txt"
SAMPLE_PDF = PROJECT_ROOT / "sample_documents" / "sample_budget_faq.pdf"

EXPECTED_PHRASES = [
    "SMARTBUDGET JA - SAMPLE FINANCIAL GUIDE",
    "Net Pay:",
    "The amount an employee receives after deductions",
    "Gross Pay:",
    "The total earnings before deductions.",
    "Utilities:",
    "and water expenses.",
    "Budget Balance:",
    "have been subtracted from income.",
]


class FakeUpload:
    def __init__(self, name, content, size=None):
        self.name = name
        self._content = content
        self.size = len(content) if size is None else size

    def getvalue(self):
        return self._content


class DocumentServiceTests(unittest.TestCase):
    def test_sample_txt_extraction_matches_the_lesson_text(self):
        text = extract_document_text(SAMPLE_TXT)
        self.assertEqual(text, SAMPLE_TXT.read_text(encoding="utf-8"))
        for phrase in EXPECTED_PHRASES:
            self.assertIn(phrase, text)

    def test_sample_pdf_contains_the_same_information(self):
        self.assertTrue(SAMPLE_PDF.exists(), "Sample PDF was not generated.")
        text = extract_document_text(SAMPLE_PDF)
        for phrase in EXPECTED_PHRASES:
            self.assertIn(phrase, text)

    def test_invalid_extension_is_rejected(self):
        upload = FakeUpload("notes.exe", b"hello")
        with self.assertRaises(ValueError):
            validate_file(upload)

    def test_oversized_file_is_rejected(self):
        upload = FakeUpload("bill.pdf", b"%PDF-1.4", size=MAX_FILE_SIZE + 1)
        with self.assertRaises(ValueError):
            validate_file(upload)

    def test_empty_file_is_rejected(self):
        upload = FakeUpload("empty.txt", b"")
        with self.assertRaises(ValueError):
            validate_file(upload)

    def test_invalid_signatures_are_rejected(self):
        samples = [
            FakeUpload("bad.pdf", b"not a pdf"),
            FakeUpload("bad.png", b"not a png"),
            FakeUpload("bad.jpg", b"not a jpeg"),
            FakeUpload("bad.jpeg", b"not a jpeg"),
            FakeUpload("bad.txt", b"\xff\xfe"),
        ]
        for upload in samples:
            with self.assertRaises(ValueError):
                validate_file(upload)

    def test_save_uses_a_generated_filename(self):
        with tempfile.TemporaryDirectory() as directory:
            content = "Rent is fictional.\n".encode("utf-8")
            upload = FakeUpload(r"..\secret.txt", content)
            path = save_uploaded_file(upload, directory)
            self.assertEqual(path.parent, Path(directory))
            self.assertNotIn("secret", path.name)
            self.assertTrue(path.name.endswith(".txt"))
            self.assertEqual(path.read_bytes(), content)
            self.assertIn("Rent is fictional.", extract_document_text(path))

    def test_corrupt_pdf_raises_a_readable_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.pdf"
            path.write_bytes(b"%PDF-1.4\nthis is not a real pdf")
            with self.assertRaises(ValueError):
                extract_document_text(path)

    def test_text_pdf_created_with_pymupdf_can_be_extracted(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "note.pdf"
            document = pymupdf.open()
            page = document.new_page()
            page.insert_text((72, 72), "Gross Pay:\nThe total earnings before deductions.")
            document.save(path)
            document.close()
            text = extract_document_text(path)
            self.assertIn("Gross Pay:", text)
            self.assertIn("before deductions", text)

    def test_document_index_saves_category(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "documents.json"
            self.assertEqual(load_document_index(path), [])
            record = add_document_record(
                original_filename="electricity_bill.pdf",
                stored_filename="abc123.pdf",
                category="Electricity Bill",
                size_bytes=24500,
                file_path=path,
            )
            self.assertEqual(record["id"], "DOC-001")
            self.assertEqual(record["category"], "Electricity Bill")
            again = add_document_record(
                original_filename="payslip.pdf",
                stored_filename="def456.pdf",
                category="Payslip",
                size_bytes=100,
                file_path=path,
            )
            self.assertEqual(again["id"], "DOC-002")
            self.assertEqual(len(load_document_index(path)), 2)

    def test_invalid_category_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "documents.json"
            with self.assertRaises(ValueError):
                add_document_record(
                    "a.pdf",
                    "b.pdf",
                    "Bank Statement",
                    10,
                    path,
                )
            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
