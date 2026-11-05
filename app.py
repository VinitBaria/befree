"""
Bank Statement Processing & Classification System — Befree
Complete Prototype Demo: Extract, Classify (Rule-Based), and Export.

Run: python app.py
Open: http://localhost:5000
"""
import os
import re
import io
import csv
import uuid
import tempfile
from datetime import datetime
from typing import Optional

from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import pdfplumber
import pytesseract
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Auto-locate Tesseract OCR on Windows if available
for t_path in [
    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
    r'C:\Users\vinit baria\AppData\Local\Programs\Tesseract-OCR\tesseract.exe',
]:
    if os.path.exists(t_path):
        pytesseract.pytesseract.tesseract_cmd = t_path
        break

app = Flask(__name__)
CORS(app)

_sessions = {}

# ─────────────────────────────────────────────────────────────────────────────
# 1. Classification Categories & Rule-Based Matching (No ML/LLM)
# ─────────────────────────────────────────────────────────────────────────────
CATEGORIES = {
    "UPI Transfer":               ["upi", "bhim", "gpay", "phonepe", "paytm"],
    "NEFT / RTGS Transfer":       ["neft", "rtgs", "imps", "fund transfer"],
    "ATM Withdrawal":             ["atm", "cash withdrawal", "atm wdl", "wdl"],
    "Salary / Income":            ["salary", "payroll", "wages", "stipend"],
    "EMI / Loan Payment":         ["emi", "loan", "repayment", "nach"],
    "Utility Bills":              ["electricity", "bescom", "msedcl", "water bill", "gas bill", "broadband"],
    "Mobile / Recharge":          ["recharge", "airtel", "jio", "vodafone", "bsnl"],
    "Insurance":                  ["insurance", "lic", "premium", "policy"],
    "Investments / Mutual Funds": ["mutual fund", "sip", "groww", "zerodha", "nps", "ppf"],
    "Shopping / E-commerce":      ["amazon", "flipkart", "myntra", "ajio", "nykaa"],
    "Groceries":                  ["bigbasket", "blinkit", "dmart", "zepto", "grofers"],
    "Food & Dining":              ["swiggy", "zomato", "restaurant", "dominos", "kfc", "mcdonald", "cafe"],
    "Fuel / Transport":           ["petrol", "diesel", "hpcl", "bpcl", "uber", "ola", "fastag", "irctc", "metro"],
    "Healthcare / Medical":       ["hospital", "pharmacy", "apollo", "medplus", "clinic", "diagnostic", "medicine"],
    "Education":                  ["school", "college", "tuition", "byju", "udemy", "fees"],
    "Entertainment / OTT":        ["netflix", "hotstar", "spotify", "bookmyshow", "pvr", "inox", "prime"],
    "Travel / Hospitality":       ["oyo", "makemytrip", "goibibo", "flight", "hotel"],
    "Bank Charges / Fees":        ["charge", "fee", "penalty", "gst", "tds", "maintenance"],
    "Cash Deposit":               ["cash deposit", "cdm deposit", "counter deposit"],
    "Cheque":                     ["cheque", "chq", "clearing", "ecs"],
    "Refund / Reversal":          ["refund", "reversal", "cashback", "return"],
    "Rent":                       ["rent", "rental", "lease"],
}

CATEGORY_COLORS = {
    'UPI Transfer': 'D6EAF8', 'NEFT / RTGS Transfer': 'D1F2EB', 'ATM Withdrawal': 'FADBD8',
    'Salary / Income': 'D5F5E3', 'EMI / Loan Payment': 'FDEBD0', 'Utility Bills': 'F9E79F',
    'Mobile / Recharge': 'D7BDE2', 'Insurance': 'AED6F1', 'Investments / Mutual Funds': 'A9DFBF',
    'Shopping / E-commerce': 'F9E0D9', 'Groceries': 'FDFEFE', 'Food & Dining': 'FAD7A0',
    'Fuel / Transport': 'ABEBC6', 'Healthcare / Medical': 'F1948A', 'Education': 'A9CCE3',
    'Entertainment / OTT': 'C39BD3', 'Travel / Hospitality': 'A2D9CE', 'Bank Charges / Fees': 'F5B7B1',
    'Cash Deposit': 'A9DFBF', 'Cheque': 'D2B4DE', 'Refund / Reversal': 'A3E4D7',
    'Rent': 'F7DC6F', 'Other': 'EAECEE',
}


def classify_transaction(description: str) -> str:
    """Classify description using rule-based keyword matching."""
    if not description:
        return "Other"
    text = str(description).lower().strip()
    for category, keywords in CATEGORIES.items():
        for kw in keywords:
            if len(kw) <= 3:
                if re.search(r'\b' + re.escape(kw) + r'\b', text):
                    return category
            elif kw in text:
                return category
    return "Other"


def classify_all(transactions: list) -> list:
    for t in transactions:
        t["category"] = classify_transaction(t.get("description", ""))
    return transactions


# ─────────────────────────────────────────────────────────────────────────────
# 2. PDF Extraction (Text & Scanned Image OCR)
# ─────────────────────────────────────────────────────────────────────────────
DATE_REGEX = re.compile(
    r'\d{2}[/-]\d{2}[/-]\d{4}|\d{4}[/-]\d{2}[/-]\d{2}|\d{2}[/-]\d{2}[/-]\d{2}|\d{2}\s+\w{3}\s+\d{4}|\w{3}\s+\d{2},?\s+\d{4}'
)

ACCOUNT_PATTERNS = {
    'account_number': [
        r'(?:Account\s*(?:Number|No\.?|#)\s*[:\-]?\s*)(\d[\d\s\-]{6,20})',
        r'(?:A/c\s*(?:No\.?|#)?\s*[:\-]?\s*)(\d[\d\s\-]{6,20})',
    ],
    'account_holder': [
        r'(?:Name\s*[:\-]\s*)([A-Z][A-Za-z\s\.]{3,50})',
        r'(?:Customer\s*Name\s*[:\-]\s*)([A-Z][A-Za-z\s\.]{3,50})',
        r'(?:Account\s*Holder\s*[:\-]\s*)([A-Z][A-Za-z\s\.]{3,50})',
    ],
    'ifsc': [r'\b([A-Z]{4}0[A-Z0-9]{6})\b'],
    'bank_name': [
        r'(?:Bank\s*Name\s*[:\-]\s*)([A-Za-z\s]+)',
        r'^([A-Z][A-Za-z\s]+Bank(?:\s+Ltd\.?)?)',
    ],
    'statement_period': [
        r'(?:Statement\s*(?:Period|Date)\s*[:\-]\s*)([\d/\-\s\w]+(?:to|-)[\d/\-\s\w]+)',
        r'(?:From\s*[:\-]?\s*)([\d/\-]+)\s+(?:To|to)\s+([\d/\-]+)',
    ],
}


def _clean_amount(raw: str) -> Optional[float]:
    if not raw:
        return None
    cleaned = re.sub(r'(?i)(cr|dr|debit|credit)', '', raw.strip().replace(',', '').replace(' ', ''))
    try:
        return float(cleaned)
    except ValueError:
        return None


def _parse_date(raw: str) -> str:
    raw = raw.strip()
    for fmt in ('%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d/%m/%y', '%d %b %Y', '%b %d, %Y'):
        try:
            return datetime.strptime(raw, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return raw


def extract_account_details(text: str) -> dict:
    details = {'account_holder': '', 'account_number': '', 'ifsc': '', 'bank_name': '', 'statement_period': ''}
    for field, patterns in ACCOUNT_PATTERNS.items():
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
            if m:
                details[field] = m.group(1).strip() if m.lastindex else m.group(0).strip()
                break
    return details


def extract_transactions_from_table(table: list) -> list:
    if not table or len(table) < 2:
        return []

    header_idx, col_map = -1, {}
    for i, row in enumerate(table[:5]):
        text = ' '.join(str(c).lower() for c in row if c)
        if any(k in text for k in ['date', 'description', 'narration', 'debit', 'credit', 'balance']):
            header_idx = i
            for idx, h in enumerate([str(c).lower().strip() if c else '' for c in row]):
                if any(k in h for k in ['date', 'txn date', 'posting']):
                    col_map.setdefault('date', idx)
                elif any(k in h for k in ['description', 'narration', 'particulars', 'details']):
                    col_map.setdefault('description', idx)
                elif any(k in h for k in ['debit', 'dr', 'withdrawal']):
                    col_map.setdefault('debit', idx)
                elif any(k in h for k in ['credit', 'cr', 'deposit']):
                    col_map.setdefault('credit', idx)
                elif any(k in h for k in ['balance', 'closing']):
                    col_map.setdefault('balance', idx)
                elif any(k in h for k in ['ref', 'reference', 'chq']):
                    col_map.setdefault('reference', idx)
            break

    if header_idx == -1:
        return []

    txns = []
    for row in table[header_idx + 1:]:
        if not row:
            continue
        date_val = str(row[col_map['date']]).strip() if 'date' in col_map and col_map['date'] < len(row) and row[col_map['date']] else ''
        m = DATE_REGEX.search(date_val)
        if not m:
            continue

        def get_val(key):
            if key in col_map and col_map[key] < len(row) and row[col_map[key]] is not None:
                return str(row[col_map[key]]).strip()
            return ''

        txns.append({
            'date': _parse_date(m.group()),
            'description': get_val('description'),
            'debit': _clean_amount(get_val('debit')),
            'credit': _clean_amount(get_val('credit')),
            'balance': _clean_amount(get_val('balance')),
            'reference': get_val('reference'),
        })
    return txns


def extract_transactions_fallback(text: str) -> list:
    txns = []
    pat = re.compile(r'(\d{2}[/\-]\d{2}[/\-]\d{2,4})\s+(.+?)\s+([\d,]+\.\d{2})?\s*([\d,]+\.\d{2})?\s*([\d,]+\.\d{2})?')
    for line in text.split('\n'):
        m = pat.search(line.strip())
        if m:
            g = m.groups()
            txns.append({
                'date': _parse_date(g[0]),
                'description': g[1].strip() if g[1] else '',
                'debit': _clean_amount(g[2]),
                'credit': None,
                'balance': _clean_amount(g[3] or g[4]),
                'reference': '',
            })
    return txns


def process_pdf(pdf_path: str) -> dict:
    all_text, all_txns = [], []
    with pdfplumber.open(pdf_path) as pdf:
        # Step 1: Detect PDF type (text vs scanned image)
        sample_chars = sum(len((p.extract_text() or '').strip()) for p in pdf.pages[:3])
        pdf_type = 'image' if (sample_chars / max(1, len(pdf.pages[:3]))) < 50 else 'text'

        if pdf_type == 'image':
            # Image OCR extraction
            for p in pdf.pages:
                img = p.to_image(resolution=200).original
                text = pytesseract.image_to_string(img)
                if text:
                    all_text.append(text)
            full_text = '\n\n'.join(all_text)
            all_txns = extract_transactions_fallback(full_text)
            extraction_method = 'image_ocr'
        else:
            # Text PDF table extraction
            for p in pdf.pages:
                t = p.extract_text() or ''
                all_text.append(t)
                for tbl in p.extract_tables():
                    all_txns.extend(extract_transactions_from_table(tbl))
            full_text = '\n'.join(all_text)
            if not all_txns:
                all_txns = extract_transactions_fallback(full_text)
            extraction_method = 'text'

    acc_details = extract_account_details(full_text)
    classified_txns = classify_all(all_txns)

    return {
        'pdf_type': pdf_type,
        'extraction_method': extraction_method,
        'account_details': acc_details,
        'transactions': classified_txns,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3. Exporters (Excel & CSV)
# ─────────────────────────────────────────────────────────────────────────────
EXCEL_COLUMNS = ['Date', 'Description', 'Debit', 'Credit', 'Balance', 'Category', 'Reference']


def export_to_excel(acc: dict, txns: list) -> bytes:
    wb = openpyxl.Workbook()

    # Sheet 1: Account
    ws_acc = wb.active
    ws_acc.title = 'Account Details'
    ws_acc.merge_cells('A1:B1')
    ws_acc['A1'].value = '🏦 Bank Statement — Account Information'
    ws_acc['A1'].font = Font(bold=True, color='FFFFFF', size=13)
    ws_acc['A1'].fill = PatternFill('solid', fgColor='1A5276')

    info = [
        ('Account Holder', acc.get('account_holder', 'N/A')),
        ('Account Number', acc.get('account_number', 'N/A')),
        ('Bank Name', acc.get('bank_name', 'N/A')),
        ('IFSC Code', acc.get('ifsc', 'N/A')),
        ('Statement Period', acc.get('statement_period', 'N/A')),
        ('Processed On', datetime.now().strftime('%Y-%m-%d %H:%M')),
    ]
    for r, (k, v) in enumerate(info, start=2):
        ws_acc.cell(row=r, column=1, value=k).font = Font(bold=True)
        ws_acc.cell(row=r, column=2, value=v)
    ws_acc.column_dimensions['A'].width = 22
    ws_acc.column_dimensions['B'].width = 38

    # Sheet 2: Transactions
    ws_txn = wb.create_sheet('Transactions')
    thin = Side(style='thin')
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    hdr_fill = PatternFill('solid', fgColor='2C3E50')
    hdr_font = Font(bold=True, color='FFFFFF')

    for col_idx, col_name in enumerate(EXCEL_COLUMNS, start=1):
        c = ws_txn.cell(row=1, column=col_idx, value=col_name)
        c.fill, c.font, c.border = hdr_fill, hdr_font, border

    for r_idx, t in enumerate(txns, start=2):
        row = [t.get('date', ''), t.get('description', ''), t.get('debit', ''), t.get('credit', ''),
               t.get('balance', ''), t.get('category', 'Other'), t.get('reference', '')]
        fill = PatternFill('solid', fgColor=CATEGORY_COLORS.get(t.get('category', 'Other'), 'EAECEE'))
        for col_idx, val in enumerate(row, start=1):
            cell = ws_txn.cell(row=r_idx, column=col_idx, value=val)
            cell.fill, cell.border = fill, border
            if col_idx in (3, 4, 5):
                cell.alignment = Alignment(horizontal='right')
                if isinstance(val, (int, float)):
                    cell.number_format = '#,##0.00'

    for i, w in enumerate([12, 45, 14, 14, 14, 25, 20], start=1):
        ws_txn.column_dimensions[get_column_letter(i)].width = w
    ws_txn.freeze_panes = 'A2'

    # Sheet 3: Category Summary
    ws_sum = wb.create_sheet('Summary')
    sum_data = {}
    for t in txns:
        cat = t.get('category', 'Other')
        sum_data.setdefault(cat, {'count': 0, 'debit': 0.0, 'credit': 0.0})
        sum_data[cat]['count'] += 1
        sum_data[cat]['debit'] += t.get('debit') or 0.0
        sum_data[cat]['credit'] += t.get('credit') or 0.0

    for col_idx, h in enumerate(['Category', 'Transactions', 'Total Debit (₹)', 'Total Credit (₹)'], start=1):
        c = ws_sum.cell(row=1, column=col_idx, value=h)
        c.fill, c.font = hdr_fill, hdr_font

    for r_idx, (cat, d) in enumerate(sorted(sum_data.items()), start=2):
        fill = PatternFill('solid', fgColor=CATEGORY_COLORS.get(cat, 'EAECEE'))
        for c_idx, v in enumerate([cat, d['count'], round(d['debit'], 2), round(d['credit'], 2)], start=1):
            c = ws_sum.cell(row=r_idx, column=c_idx, value=v)
            c.fill = fill

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def export_to_csv(acc: dict, txns: list) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(['=== ACCOUNT DETAILS ==='])
    for k, v in acc.items():
        w.writerow([k.replace('_', ' ').title(), v])
    w.writerow([])
    w.writerow(['=== TRANSACTIONS ==='])
    w.writerow(EXCEL_COLUMNS)
    for t in txns:
        w.writerow([t.get('date', ''), t.get('description', ''), t.get('debit', ''), t.get('credit', ''),
                    t.get('balance', ''), t.get('category', 'Other'), t.get('reference', '')])
    return ('\ufeff' + buf.getvalue()).encode('utf-8')


# ─────────────────────────────────────────────────────────────────────────────
# 4. Flask Web Routes
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'})


@app.route('/api/process', methods=['POST'])
def handle_process():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    f = request.files['file']
    if not f.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Only PDF files are supported'}), 400

    sid = str(uuid.uuid4())
    tmp = os.path.join(tempfile.gettempdir(), f'stmt_{sid}.pdf')
    try:
        f.save(tmp)
        result = process_pdf(tmp)
        txns = result['transactions']
        acc = result['account_details']
        _sessions[sid] = {'account_details': acc, 'transactions': txns}

        cats = {}
        for t in txns:
            c = t.get('category', 'Other')
            cats[c] = cats.get(c, 0) + 1

        return jsonify({
            'session_id': sid,
            'pdf_type': result['pdf_type'],
            'extraction_method': result['extraction_method'],
            'account_details': acc,
            'transactions': txns,
            'summary': {
                'total_transactions': len(txns),
                'total_debit': round(sum(t.get('debit') or 0 for t in txns), 2),
                'total_credit': round(sum(t.get('credit') or 0 for t in txns), 2),
                'category_breakdown': cats,
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass


@app.route('/api/demo')
def handle_demo():
    demo_txns = classify_all([
        {'date': '2024-01-03', 'description': 'UPI/9876543210/PhonePe/Food', 'debit': 450.0, 'credit': None, 'balance': 24550.0, 'reference': 'UPI001'},
        {'date': '2024-01-05', 'description': 'Salary credit PAYROLL/EMP001', 'debit': None, 'credit': 55000.0, 'balance': 79550.0, 'reference': 'SAL001'},
        {'date': '2024-01-07', 'description': 'ATM WDL 123456 HDFC Mumbai', 'debit': 5000.0, 'credit': None, 'balance': 74550.0, 'reference': ''},
        {'date': '2024-01-08', 'description': 'Amazon.in purchase order', 'debit': 1299.0, 'credit': None, 'balance': 73251.0, 'reference': 'AMZ001'},
        {'date': '2024-01-10', 'description': 'BESCOM electricity bill payment', 'debit': 1850.0, 'credit': None, 'balance': 71401.0, 'reference': ''},
        {'date': '2024-01-12', 'description': 'EMI debit housing loan HDFC', 'debit': 18500.0, 'credit': None, 'balance': 52901.0, 'reference': 'EMI001'},
        {'date': '2024-01-14', 'description': 'Swiggy food order dinner', 'debit': 340.0, 'credit': None, 'balance': 52561.0, 'reference': ''},
        {'date': '2024-01-15', 'description': 'Netflix monthly subscription', 'debit': 649.0, 'credit': None, 'balance': 51912.0, 'reference': ''},
        {'date': '2024-01-18', 'description': 'LIC premium payment policy', 'debit': 3200.0, 'credit': None, 'balance': 48712.0, 'reference': ''},
        {'date': '2024-01-19', 'description': 'NEFT inward transfer RAHUL', 'debit': None, 'credit': 10000.0, 'balance': 58712.0, 'reference': 'NEFT01'},
        {'date': '2024-01-20', 'description': 'Refund Amazon order returned', 'debit': None, 'credit': 1299.0, 'balance': 60011.0, 'reference': 'RFD001'},
        {'date': '2024-01-22', 'description': 'HPCL petrol pump fuel fill', 'debit': 2000.0, 'credit': None, 'balance': 58011.0, 'reference': ''},
        {'date': '2024-01-25', 'description': 'SIP debit Groww mutual fund', 'debit': 5000.0, 'credit': None, 'balance': 53011.0, 'reference': 'SIP001'},
        {'date': '2024-01-26', 'description': 'Mobile recharge Jio prepaid', 'debit': 399.0, 'credit': None, 'balance': 52612.0, 'reference': ''},
        {'date': '2024-01-27', 'description': 'IRCTC train ticket booking', 'debit': 1200.0, 'credit': None, 'balance': 51412.0, 'reference': 'TKT001'},
        {'date': '2024-01-28', 'description': 'OYO hotel booking Bangalore', 'debit': 2500.0, 'credit': None, 'balance': 48912.0, 'reference': ''},
        {'date': '2024-01-29', 'description': 'Apollo pharmacy medicine bill', 'debit': 890.0, 'credit': None, 'balance': 48022.0, 'reference': ''},
        {'date': '2024-01-30', 'description': 'Annual maintenance fee GST', 'debit': 590.0, 'credit': None, 'balance': 47432.0, 'reference': ''},
        {'date': '2024-01-31', 'description': 'House rent payment transfer', 'debit': 12000.0, 'credit': None, 'balance': 35432.0, 'reference': ''},
    ])
    acc = {
        'account_holder': 'Rahul Sharma',
        'account_number': '1234 5678 9012',
        'bank_name': 'HDFC Bank',
        'ifsc': 'HDFC0001234',
        'statement_period': '01/01/2024 to 31/01/2024',
    }
    sid = 'demo-' + uuid.uuid4().hex[:8]
    _sessions[sid] = {'account_details': acc, 'transactions': demo_txns}

    cats = {}
    for t in demo_txns:
        c = t.get('category', 'Other')
        cats[c] = cats.get(c, 0) + 1

    return jsonify({
        'session_id': sid,
        'pdf_type': 'demo',
        'account_details': acc,
        'transactions': demo_txns,
        'summary': {
            'total_transactions': len(demo_txns),
            'total_debit': round(sum(t.get('debit') or 0 for t in demo_txns), 2),
            'total_credit': round(sum(t.get('credit') or 0 for t in demo_txns), 2),
            'category_breakdown': cats,
        }
    })


@app.route('/api/export/<sid>/<fmt>')
def handle_export(sid, fmt):
    if sid not in _sessions:
        return jsonify({'error': 'Session expired'}), 404
    acc, txns = _sessions[sid]['account_details'], _sessions[sid]['transactions']
    if fmt == 'excel':
        return send_file(io.BytesIO(export_to_excel(acc, txns)),
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         as_attachment=True, download_name='bank_statement.xlsx')
    if fmt == 'csv':
        return send_file(io.BytesIO(export_to_csv(acc, txns)),
                         mimetype='text/csv',
                         as_attachment=True, download_name='bank_statement.csv')
    return jsonify({'error': 'Invalid format'}), 400


if __name__ == '__main__':
    print("\n  Bank Statement Processor — Befree")
    print("  Running on: http://localhost:5000\n")
    app.run(debug=True, port=5000)
