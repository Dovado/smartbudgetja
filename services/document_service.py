"""Validate, store, and extract text from financial documents."""

import uuid
from pathlib import Path

import pymupdf

from services.storage_service import DOCUMENTS_FILE, load_json, save_json


PROJECT_ROOT = Path(__file__).resolve().parent.parent
UPLOAD_DIR = PROJECT_ROOT / "uploads"

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".txt",
}
MAX_FILE_SIZE = 5 * 1024 * 1024

DOCUMENT_CATEGORIES = [
    "Payslip",
    "Electricity Bill",
    "Water Bill",
    "Internet Bill",
    "Other",
]


def validate_file(uploaded_file):
    """Check extension, size, and a basic file signature.

    Returns the lowercase extension when the file is acceptable.
    """
    extension = Path(uploaded_file.name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported file extension.")
    if uploaded_file.size > MAX_FILE_SIZE:
        raise ValueError("File exceeds the 5 MB limit.")
    if uploaded_file.size == 0:
        raise ValueError("File is empty.")

    content = uploaded_file.getvalue()
    if extension == ".pdf":
        if not content.startswith(b"%PDF-"):
            raise ValueError("Invalid PDF signature.")
    elif extension == ".png":
        if not content.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError("Invalid PNG signature.")
    elif extension in {".jpg", ".jpeg"}:
        if not content.startswith(b"\xff\xd8\xff"):
            raise ValueError("Invalid JPEG signature.")
    elif extension == ".txt":
        try:
            content.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError("Text files must use UTF-8.") from None
    return extension


def save_uploaded_file(uploaded_file, upload_dir=None):
    """Store an upload under a generated filename and return its path."""
    extension = validate_file(uploaded_file)
    directory = Path(upload_dir) if upload_dir else UPLOAD_DIR
    directory.mkdir(parents=True, exist_ok=True)
    # UUID filenames avoid collisions and ignore unsafe original paths.
    safe_filename = f"{uuid.uuid4().hex}{extension}"
    file_path = directory / safe_filename
    file_path.write_bytes(uploaded_file.getvalue())
    return file_path


def extract_document_text(file_path):
    """Extract embedded text from a TXT or text-based PDF file.

    Images and scanned PDFs return an empty string. This lesson does not
    include OCR, and files are not sent to an external service.
    """
    path = Path(file_path)
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return path.read_text(encoding="utf-8")
    if suffix == ".pdf":
        text_parts = []
        try:
            with pymupdf.open(path) as document:
                for page in document:
                    text_parts.append(page.get_text())
        except Exception as error:
            raise ValueError(
                "The PDF could not be read. It may be damaged."
            ) from error
        return "\n".join(text_parts)
    return ""


def load_document_index(file_path=None):
    """Load the document category index, or an empty list if it is missing."""
    path = Path(file_path) if file_path else DOCUMENTS_FILE
    records = load_json(path, [])
    if not isinstance(records, list):
        raise ValueError(
            "Document index must be a JSON array. The saved file was not changed."
        )
    return records


def next_document_id(records):
    """Return the next DOC-001 style identifier."""
    highest = 0
    for record in records:
        doc_id = str(record.get("id", ""))
        if doc_id.startswith("DOC-") and doc_id[4:].isdigit():
            highest = max(highest, int(doc_id[4:]))
    return f"DOC-{highest + 1:03d}"


def add_document_record(
    original_filename,
    stored_filename,
    category,
    size_bytes,
    file_path=None,
):
    """Append one document metadata record and return it."""
    if category not in DOCUMENT_CATEGORIES:
        raise ValueError("Choose a valid document category.")

    path = Path(file_path) if file_path else DOCUMENTS_FILE
    records = load_document_index(path)
    record = {
        "id": next_document_id(records),
        "original_filename": original_filename,
        "stored_filename": stored_filename,
        "category": category,
        "size_bytes": int(size_bytes),
    }
    records.append(record)
    save_json(path, records)
    return record
