# 🏦 Bank Statement Processor — Befree

A simple, production-ready prototype system for processing bank statements in PDF format (both text-based and scanned image), extracting financial data, classifying transactions using rule-based heuristics (no LLM/ML complexity), and exporting to Excel & CSV.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the App
```bash
python app.py
```
Open **http://localhost:5000** in your browser.

---

## 📁 Clean Project Structure

```
Befree/
├── app.py              # Flask server, PDF extractor, rule-based classifier & exporters
├── requirements.txt    # Minimal project dependencies
├── README.md           # Documentation
├── .gitignore          # Git exclusions
└── templates/
    └── index.html      # Responsive web interface (demo, upload, filters, tables)
```

---

## 💡 Key Features

| Feature | Details |
|---|---|
| **PDF Auto-Detection** | Distinguishes between digital text PDFs and scanned raster images |
| **Data Extraction** | Extracts Account Holder, Account Number, IFSC, Statement Period, and transaction tables |
| **Transaction Classification** | 22 categories categorized via deterministic keyword rules with word boundaries (No LLMs) |
| **Export Formats** | Color-coded Excel (.xlsx) with 3 sheets (Account, Transactions, Summary) and UTF-8 CSV (.csv) |
| **Instant Demo Mode** | One-click sample statement loader to evaluate the full flow without uploading |
| **Interactive UI** | Real-time search, category dropdown filter, and Debit/Credit toggles |

---

## 🏷️ Classification Categories

UPI Transfer, NEFT / RTGS Transfer, ATM Withdrawal, Salary / Income, EMI / Loan Payment, Utility Bills, Mobile / Recharge, Insurance, Investments / Mutual Funds, Shopping / E-commerce, Groceries, Food & Dining, Fuel / Transport, Healthcare / Medical, Education, Entertainment / OTT, Travel / Hospitality, Bank Charges / Fees, Cash Deposit, Cheque, Refund / Reversal, Rent, Other

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Web UI |
| `GET` | `/api/health` | Health check endpoint |
| `POST` | `/api/process` | Upload and process PDF statement |
| `GET` | `/api/demo` | Load sample demo data |
| `GET` | `/api/export/<id>/excel` | Download processed data in Excel format |
| `GET` | `/api/export/<id>/csv` | Download processed data in CSV format |
