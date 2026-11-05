# Bank Statement Processor

A simple prototype to extract, classify, and export bank statement PDFs (text & scanned) without LLMs.

---

## How to Run

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the app:**
   ```bash
   python app.py
   ```

3. **Open in browser:**
   Go to **http://localhost:5000**

---

## Features

- **Upload Bank Statements**: Supports both text-based and scanned image PDFs.
- **Auto-Detection**: Automatically detects whether a PDF is digital text or scanned.
- **Data Extraction**: Extracts account details (name, account number, IFSC) and transactions (date, description, debit, credit, balance).
- **Rule-Based Classification**: Categorizes transactions into 22 categories using keyword rules (No LLM).
- **Export Data**: Download processed results as formatted Excel (`.xlsx`) or CSV (`.csv`).
- **Demo Mode**: Test immediately with built-in sample data (no file upload required).

---

## Project Files

- `app.py` — Backend server, PDF extractor, rule-based classifier, and export handlers.
- `templates/index.html` — Web interface with upload, demo mode, filters, and tables.
- `requirements.txt` — Python dependencies.
