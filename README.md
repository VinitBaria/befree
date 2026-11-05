# 🏦 Bank Statement Processor — Befree

A clean, production-ready prototype for extracting, classifying, and exporting bank statement data — **no LLMs used**.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Application
```bash
python app.py
```
Open **http://localhost:5000** in your browser.

---

## Project Structure

```
Befree/
├── app.py                      # Flask backend & API routes
├── requirements.txt            # Dependencies
├── README.md                   # Documentation
├── .gitignore
│
├── templates/
│   └── index.html              # Frontend Web UI
│
├── processors/
│   ├── pdf_detector.py         # Auto-detects text vs image (scanned) PDF
│   ├── text_extractor.py       # Table & text extraction via pdfplumber
│   ├── image_extractor.py      # OCR extraction via Tesseract
│   └── classifier.py           # Fast rule-based transaction classifier
│
└── exporters/
    └── exporter.py             # Formatted Excel (.xlsx) & CSV export
```

---

## Features

| Feature | Details |
|---|---|
| **PDF Type Detection** | Automatically determines if PDF is digital text or scanned image |
| **Data Extraction** | Extracts Account Holder, Account Number, IFSC, Period, and all transactions |
| **Classification** | 22 categories using keyword-based heuristic rules (no LLMs / no complex ML) |
| **Export Formats** | Color-coded Excel with 3 sheets (Account, Transactions, Summary) & CSV |
| **Demo Mode** | Built-in sample statement to test instantly without uploading a PDF |
| **Filtering** | Interactive search, category filter, and debit/credit filters |

## Categories Covered

UPI Transfer, NEFT/RTGS, ATM Withdrawal, Salary/Income, EMI/Loan, Utility Bills, Mobile/Recharge, Insurance, Investments/MF, Shopping/E-commerce, Groceries, Food & Dining, Fuel/Transport, Healthcare, Education, Entertainment/OTT, Travel, Bank Charges, Cash Deposit, Cheque, Refund/Reversal, Rent, Other

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Web UI |
| GET | `/api/health` | Health check |
| POST | `/api/process` | Upload and process bank statement PDF |
| GET | `/api/demo` | Load sample demo data |
| GET | `/api/export/{id}/excel` | Download Excel (.xlsx) |
| GET | `/api/export/{id}/csv` | Download CSV (.csv) |
