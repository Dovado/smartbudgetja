# SmartBudget JA

SmartBudget JA is a Jamaican personal finance management and knowledge retrieval application. It is a learning project built with Python and Streamlit. The app records monthly income and expenses, stores the records in local JSON files, extracts text from sample financial documents, and retrieves answers from a keyword-based knowledge base.

## Features

The sidebar opens five screens:

- **Dashboard** shows the selected month's income, expenses, balance, and a category chart.
- **Income & Expenses** saves monthly income, adds and deletes expenses, and summarizes the selected month.
- **Documents** checks an uploaded file, stores it locally, extracts embedded text, and records a document category.
- **Knowledge Base** lists financial definitions and lets you add a new record.
- **Ask SmartBudget** ranks stored knowledge records for a question. It does not generate a new answer.

## Technologies

- Python 3
- Streamlit
- PyMuPDF
- JSON

## Installation

From the project folder in Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Running the application

```powershell
python -m streamlit run app.py
```

## Running tests

```powershell
python -m unittest discover -s tests -v
```

## Demonstration data

Income & Expenses includes an optional control that loads fictional October 2026 records: net income of J$180,000.00, six expenses totaling J$112,500.00, and a remaining balance of J$67,500.00. Loading it replaces the current financial file only after you confirm.

Sample files in `sample_documents/` contain the same short financial guide as plain text and as a text-based PDF.

## Project organization

- `app.py` configures Streamlit, loads saved finances, and routes the five screens.
- `screens/` contains the user interface for each screen.
- `services/` contains calculations, JSON storage, document checks, and knowledge search.
- `data/` contains the financial records, knowledge records, and document index.
- `uploads/` stores uploaded documents under generated filenames.
- `sample_documents/` contains the fictional text and PDF used to try extraction.

## Important limitations

- Data is stored locally in JSON.
- The application is intended for educational use.
- Uploaded documents should be fictional or redacted.
- Scanned PDFs may require OCR. This project does not include OCR.
- Knowledge retrieval is keyword-based. It is not a generative AI chatbot.
- It is not a financial advisory service.
- Local JSON storage is not intended as a multi-user production database.
