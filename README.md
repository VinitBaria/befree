# 🏦 Bank Statement Processor — Befree

A simple, fully functional prototype system capable of processing bank statements in PDF format (both text-based and scanned image), extracting financial data, classifying transactions using a heuristic rule-based approach (Non-LLM), and exporting the processed data into structured Excel (.xlsx) and CSV (.csv) formats.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start Application
```bash
python app.py
```
Open **http://localhost:5000** in your browser.

---

## 📁 Project Structure

```
Befree/
├── app.py              # Self-contained backend: PDF extraction, rule classifier, exporters & API
├── requirements.txt    # Dependencies (Flask, pdfplumber, openpyxl, pytesseract, Pillow)
├── README.md           # Documentation
├── .gitignore          # Git exclusions
└── templates/
    └── index.html      # Single-page Web UI (demo mode, upload, filters, tables)
```

---

## ⚙️ Features Implemented

| Feature | Description |
|---|---|
| **Input Handling** | Accepts bank statements in PDF format (multiple banks and layouts). |
| **PDF Auto-Detection** | Automatically detects whether the PDF is text-based or scanned (image-based). |
| **Data Extraction** | Extracts account details (Name, Account Number, IFSC, Period) and transaction tables (Date, Description, Debit, Credit, Balance). |
| **Rule-Based Classification** | Categorizes transactions across 22 categories using keyword matching with word-boundary protection (No LLM). |
| **Data Export** | Exports data into formatted Excel (.xlsx) with 3 sheets (Account, Transactions, Summary) and CSV (.csv). |
| **Instant Demo Mode** | Built-in sample statement to test the full flow without uploading a file. |
| **Interactive UI** | Live text search, category dropdown filter, and Debit/Credit filter toggles. |

---

## 🏷️ Transaction Categories

* UPI Transfer
* NEFT / RTGS Transfer
* ATM Withdrawal
* Salary / Income
* EMI / Loan Payment
* Utility Bills
* Mobile / Recharge
* Insurance
* Investments / Mutual Funds
* Shopping / E-commerce
* Groceries
* Food & Dining
* Fuel / Transport
* Healthcare / Medical
* Education
* Entertainment / OTT
* Travel / Hospitality
* Bank Charges / Fees
* Cash Deposit
* Cheque
* Refund / Reversal
* Rent
* Other

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Web application interface |
| `GET` | `/api/health` | Health check endpoint |
| `POST` | `/api/process` | Upload and process bank statement PDF |
| `GET` | `/api/demo` | Load sample demo data |
| `GET` | `/api/export/<id>/excel` | Download processed data in Excel format |
| `GET` | `/api/export/<id>/csv` | Download processed data in CSV format |
