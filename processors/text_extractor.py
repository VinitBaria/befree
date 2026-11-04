"""
Text PDF Extractor - Extracts account details and transactions from text-based PDFs
using pdfplumber with multi-bank pattern support.
"""
import re
import pdfplumber
from datetime import datetime
from typing import Optional


# ── Date patterns used across Indian & international banks ──────────────────
DATE_PATTERNS = [
    r'\d{2}[/-]\d{2}[/-]\d{4}',   # DD/MM/YYYY or DD-MM-YYYY
    r'\d{4}[/-]\d{2}[/-]\d{2}',   # YYYY-MM-DD
    r'\d{2}[/-]\d{2}[/-]\d{2}',   # DD/MM/YY
    r'\d{2}\s+\w{3}\s+\d{4}',     # DD Mon YYYY
    r'\w{3}\s+\d{2},?\s+\d{4}',   # Mon DD, YYYY
    r'\d{2}\w{3}\d{4}',            # 01Jan2024
]
DATE_REGEX = re.compile('|'.join(DATE_PATTERNS))

# ── Account detail patterns ──────────────────────────────────────────────────
ACCOUNT_PATTERNS = {
    'account_number': [
        r'(?:Account\s*(?:Number|No\.?|#)\s*[:\-]?\s*)(\d[\d\s\-]{6,20})',
        r'(?:A/c\s*(?:No\.?|#)?\s*[:\-]?\s*)(\d[\d\s\-]{6,20})',
        r'(?:Acct\.?\s*(?:No\.?|#)?\s*[:\-]?\s*)(\d[\d\s\-]{6,20})',
    ],
    'account_holder': [
        r'(?:Name\s*[:\-]\s*)([A-Z][A-Za-z\s\.]{3,50})',
        r'(?:Customer\s*Name\s*[:\-]\s*)([A-Z][A-Za-z\s\.]{3,50})',
        r'(?:Account\s*Holder\s*[:\-]\s*)([A-Z][A-Za-z\s\.]{3,50})',
    ],
    'ifsc': [
        r'\b([A-Z]{4}0[A-Z0-9]{6})\b',
    ],
    'bank_name': [
        r'(?:Bank\s*Name\s*[:\-]\s*)([A-Za-z\s]+)',
        r'^([A-Z][A-Za-z\s]+Bank(?:\s+Ltd\.?)?)',
    ],
    'statement_period': [
        r'(?:Statement\s*(?:Period|Date)\s*[:\-]\s*)([\d/\-\s\w]+(?:to|-)[\d/\-\s\w]+)',
        r'(?:From\s*[:\-]?\s*)([\d/\-]+)\s+(?:To|to)\s+([\d/\-]+)',
        r'(?:Period\s*[:\-]\s*)([\d/\-\w\s]+)',
    ],
}


def _clean_amount(raw: str) -> Optional[float]:
    """Convert string like '1,23,456.78' or '1234.56 Cr' to float."""
    if not raw:
        return None
    raw = raw.strip().replace(',', '').replace(' ', '')
    raw = re.sub(r'(?i)(cr|dr|debit|credit)', '', raw)
    try:
        return float(raw)
    except ValueError:
        return None


def _parse_date(raw: str) -> str:
    """Normalize various date formats to YYYY-MM-DD."""
    raw = raw.strip()
    formats = [
        '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%Y/%m/%d',
        '%d/%m/%y', '%d-%m-%y', '%d %b %Y', '%b %d, %Y',
        '%b %d %Y', '%d%b%Y',
    ]
    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return raw  # Return as-is if parsing fails


def extract_account_details(text: str) -> dict:
    """Extract account metadata from full statement text."""
    details = {
        'account_holder': '',
        'account_number': '',
        'ifsc': '',
        'bank_name': '',
        'statement_period': '',
    }
    for field, patterns in ACCOUNT_PATTERNS.items():
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                details[field] = match.group(1).strip() if match.lastindex else match.group(0).strip()
                break
    return details


def _is_transaction_row(cells: list) -> bool:
    """Heuristic: a row is a transaction if it starts with a date-like string."""
    if not cells:
        return False
    first = str(cells[0]).strip()
    return bool(DATE_REGEX.match(first))


def extract_transactions_from_table(table: list) -> list:
    """
    Parse a pdfplumber table (list of rows) into transaction dicts.
    Handles variable column orders by detecting header row.
    """
    if not table or len(table) < 2:
        return []

    transactions = []
    header_row = None
    header_idx = 0

    # Find header row
    for i, row in enumerate(table[:5]):
        row_text = ' '.join(str(c).lower() for c in row if c)
        if any(kw in row_text for kw in ['date', 'description', 'narration', 'debit', 'credit', 'balance']):
            header_row = [str(c).lower().strip() if c else '' for c in row]
            header_idx = i
            break

    if header_row is None:
        return []

    # Map column positions
    col_map = {}
    for i, h in enumerate(header_row):
        if any(k in h for k in ['date', 'value date', 'txn date', 'posting']):
            col_map.setdefault('date', i)
        elif any(k in h for k in ['description', 'narration', 'particulars', 'details', 'remarks', 'transaction']):
            col_map.setdefault('description', i)
        elif any(k in h for k in ['debit', 'dr', 'withdrawal', 'paid out']):
            col_map.setdefault('debit', i)
        elif any(k in h for k in ['credit', 'cr', 'deposit', 'paid in']):
            col_map.setdefault('credit', i)
        elif any(k in h for k in ['balance', 'running bal', 'closing']):
            col_map.setdefault('balance', i)
        elif any(k in h for k in ['cheque', 'chq', 'ref', 'reference']):
            col_map.setdefault('reference', i)

    # Extract data rows
    for row in table[header_idx + 1:]:
        if not row or all(c is None or str(c).strip() == '' for c in row):
            continue

        def get_cell(key):
            idx = col_map.get(key)
            if idx is not None and idx < len(row):
                val = row[idx]
                return str(val).strip() if val is not None else ''
            return ''

        date_raw = get_cell('date')
        # Skip rows that don't start with a date
        if not DATE_REGEX.search(date_raw):
            continue

        txn = {
            'date': _parse_date(DATE_REGEX.search(date_raw).group()),
            'description': get_cell('description') or get_cell('narration'),
            'debit': _clean_amount(get_cell('debit')),
            'credit': _clean_amount(get_cell('credit')),
            'balance': _clean_amount(get_cell('balance')),
            'reference': get_cell('reference'),
        }
        transactions.append(txn)

    return transactions


def extract_transactions_text_fallback(text: str) -> list:
    """
    Regex-based fallback when table extraction fails.
    Tries to parse lines that look like transactions.
    """
    transactions = []
    # Pattern: date | description | optional amounts | balance
    pattern = re.compile(
        r'(\d{2}[/\-]\d{2}[/\-]\d{2,4})\s+'      # date
        r'(.+?)\s+'                                  # description
        r'([\d,]+\.\d{2})?\s*'                      # debit/credit
        r'([\d,]+\.\d{2})?\s*'                      # balance or second amount
        r'([\d,]+\.\d{2})?'                          # optional balance
    )
    for line in text.split('\n'):
        m = pattern.search(line.strip())
        if m:
            groups = m.groups()
            txn = {
                'date': _parse_date(groups[0]),
                'description': groups[1].strip() if groups[1] else '',
                'debit': _clean_amount(groups[2]),
                'credit': None,
                'balance': _clean_amount(groups[3] or groups[4]),
                'reference': '',
            }
            transactions.append(txn)
    return transactions


def extract_from_text_pdf(pdf_path: str) -> dict:
    """
    Main entry point for text-based PDF extraction.
    Returns account details + list of transactions.
    """
    all_text = []
    all_transactions = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ''
            all_text.append(text)

            # Try table extraction first
            tables = page.extract_tables()
            for table in tables:
                txns = extract_transactions_from_table(table)
                all_transactions.extend(txns)

    full_text = '\n'.join(all_text)
    account_details = extract_account_details(full_text)

    # Fallback to regex if no transactions found via tables
    if not all_transactions:
        all_transactions = extract_transactions_text_fallback(full_text)

    return {
        'account_details': account_details,
        'transactions': all_transactions,
        'extraction_method': 'text',
    }

