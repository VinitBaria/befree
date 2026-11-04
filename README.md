# 🏦 Bank Statement Processor — Befree

A simple, production-ready prototype for extracting, classifying, and exporting bank statement data — **no LLMs used**.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the System
**Windows:** Double-click `start.bat`

Or manually:
```bash
python app.py          # Start backend (port 5000)
# Open index.html in browser
```

### 3. Test with Sample PDF
```bash
python generate_sample_pdf.py    # Creates sample_bank_statement.pdf
```

---

## Project Structure

```
Befree/
├── app.py                      # Flask backend API
├── index.html                  # Frontend (single-file UI)
├── start.bat                   # One-click launcher (Windows)
├── requirements.txt
├── generate_sample_pdf.py      # Sample PDF generator
├── sample_bank_statement.pdf   # Generated sample
│
├── processors/
│   ├── pdf_detector.py         # Auto-detect text vs image PDF
│   ├── text_extractor.py       # pdfplumber-based text extraction
│   ├── image_extractor.py      # OCR-based extraction (pytesseract)
│   └── classifier.py           # Heuristic + ML classifier
│
└── exporters/
    └── exporter.py             # Excel (.xlsx) + CSV export
```

---

## Features

| Feature | Details |
|---|---|
| **PDF Type Detection** | Auto-detects text-based vs scanned (image) PDFs |
| **Text PDF Extraction** | pdfplumber — table parsing + regex fallback |
| **Image PDF Extraction** | pdf2image + Tesseract OCR with preprocessing |
| **Multi-bank Support** | Pattern-based for HDFC, SBI, ICICI, Axis, etc. |
| **Classification** | 24 categories, heuristic rules + TF-IDF/Naive Bayes ML |
| **Export** | Color-coded Excel with 3 sheets + CSV with BOM |
| **Demo Mode** | Load sample data without uploading any PDF |
| **Filtering** | Search, category filter, debit/credit filter |

## Classification Categories (24)

UPI Transfer, NEFT/RTGS, ATM Withdrawal, Salary/Income, EMI/Loan, Utility Bills, Mobile/Recharge, Insurance, Investments/MF, Shopping/E-commerce, Groceries, Food & Dining, Fuel/Transport, Healthcare, Education, Entertainment/OTT, Travel, Bank Charges, Cash Deposit, Cheque, Self Transfer, Refund/Reversal, Rent, Other

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| POST | `/api/process` | Upload & process PDF |
| GET | `/api/demo` | Load demo data |
| GET | `/api/export/{id}/excel` | Download Excel |
| GET | `/api/export/{id}/csv` | Download CSV |

## OCR Requirements (for scanned PDFs)

- Install [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) for Windows
- Install [Poppler for Windows](https://github.com/oschwartz10612/poppler-windows/releases)
- Add both to system PATH

