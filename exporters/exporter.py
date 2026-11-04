"""
Exporters - Export transactions to Excel (.xlsx) and CSV (.csv)
"""
import csv
import io
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


COLUMNS = [
    'Date', 'Description', 'Debit', 'Credit', 'Balance',
    'Category', 'Confidence', 'Classification Method', 'Reference'
]

CATEGORY_COLORS = {
    'UPI Transfer':              'D6EAF8',
    'NEFT / RTGS Transfer':      'D1F2EB',
    'ATM Withdrawal':            'FADBD8',
    'Salary / Income':           'D5F5E3',
    'EMI / Loan Payment':        'FDEBD0',
    'Utility Bills':             'F9E79F',
    'Mobile / Recharge':         'D7BDE2',
    'Insurance':                 'AED6F1',
    'Investments / Mutual Funds':'A9DFBF',
    'Shopping / E-commerce':     'F9E0D9',
    'Groceries':                 'FDFEFE',
    'Food & Dining':             'FAD7A0',
    'Fuel / Transport':          'ABEBC6',
    'Healthcare / Medical':      'F1948A',
    'Education':                 'A9CCE3',
    'Entertainment / OTT':       'C39BD3',
    'Travel / Hospitality':      'A2D9CE',
    'Bank Charges / Fees':       'F5B7B1',
    'Cash Deposit':              'A9DFBF',
    'Cheque':                    'D2B4DE',
    'Self Transfer':             'D5D8DC',
    'Refund / Reversal':         'A3E4D7',
    'Rent':                      'F7DC6F',
    'Other':                     'EAECEE',
}


def _row_from_txn(txn: dict) -> list:
    return [
        txn.get('date', ''),
        txn.get('description', ''),
        txn.get('debit', ''),
        txn.get('credit', ''),
        txn.get('balance', ''),
        txn.get('category', 'Other'),
        txn.get('confidence', ''),
        txn.get('classification_method', ''),
        txn.get('reference', ''),
    ]


def export_to_excel(account_details: dict, transactions: list) -> bytes:
    """
    Generate an Excel workbook with:
    - Sheet 1: Account Details
    - Sheet 2: Transactions (color-coded by category)
    - Sheet 3: Category Summary
    Returns bytes.
    """
    wb = openpyxl.Workbook()

    # ── Sheet 1: Account Details ─────────────────────────────────────────────
    ws_acc = wb.active
    ws_acc.title = 'Account Details'
    header_font = Font(bold=True, color='FFFFFF', size=12)
    header_fill = PatternFill('solid', fgColor='2C3E50')
    title_fill = PatternFill('solid', fgColor='1A5276')

    ws_acc.merge_cells('A1:B1')
    title_cell = ws_acc['A1']
    title_cell.value = '🏦 Bank Statement — Account Information'
    title_cell.font = Font(bold=True, color='FFFFFF', size=14)
    title_cell.fill = title_fill
    title_cell.alignment = Alignment(horizontal='center')

    fields = [
        ('Account Holder', account_details.get('account_holder', 'N/A')),
        ('Account Number', account_details.get('account_number', 'N/A')),
        ('Bank Name', account_details.get('bank_name', 'N/A')),
        ('IFSC Code', account_details.get('ifsc', 'N/A')),
        ('Statement Period', account_details.get('statement_period', 'N/A')),
        ('Extracted On', datetime.now().strftime('%Y-%m-%d %H:%M')),
    ]
    for i, (label, value) in enumerate(fields, start=2):
        ws_acc.cell(row=i, column=1, value=label).font = Font(bold=True)
        ws_acc.cell(row=i, column=2, value=value)

    ws_acc.column_dimensions['A'].width = 25
    ws_acc.column_dimensions['B'].width = 40

    # ── Sheet 2: Transactions ─────────────────────────────────────────────────
    ws_txn = wb.create_sheet('Transactions')
    thin = Side(style='thin')
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    # Header row
    for col_idx, col_name in enumerate(COLUMNS, start=1):
        cell = ws_txn.cell(row=1, column=col_idx, value=col_name)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')
        cell.border = border

    # Data rows
    for row_idx, txn in enumerate(transactions, start=2):
        row_data = _row_from_txn(txn)
        category = txn.get('category', 'Other')
        fill_color = CATEGORY_COLORS.get(category, 'EAECEE')
        fill = PatternFill('solid', fgColor=fill_color)

        for col_idx, value in enumerate(row_data, start=1):
            cell = ws_txn.cell(row=row_idx, column=col_idx, value=value)
            cell.fill = fill
            cell.border = border
            if col_idx in (3, 4, 5):  # Amounts: right-align
                cell.alignment = Alignment(horizontal='right')
                if isinstance(value, float):
                    cell.number_format = '#,##0.00'

    # Auto-fit columns
    col_widths = [12, 50, 14, 14, 14, 25, 12, 22, 20]
    for i, width in enumerate(col_widths, start=1):
        ws_txn.column_dimensions[get_column_letter(i)].width = width

    # Freeze header row
    ws_txn.freeze_panes = 'A2'

    # ── Sheet 3: Category Summary ─────────────────────────────────────────────
    ws_sum = wb.create_sheet('Category Summary')
    summary_data = {}
    for txn in transactions:
        cat = txn.get('category', 'Other')
        if cat not in summary_data:
            summary_data[cat] = {'count': 0, 'total_debit': 0.0, 'total_credit': 0.0}
        summary_data[cat]['count'] += 1
        summary_data[cat]['total_debit'] += txn.get('debit') or 0.0
        summary_data[cat]['total_credit'] += txn.get('credit') or 0.0

    sum_headers = ['Category', 'Transaction Count', 'Total Debit (₹)', 'Total Credit (₹)']
    for col_idx, h in enumerate(sum_headers, start=1):
        cell = ws_sum.cell(row=1, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')

    for row_idx, (cat, data) in enumerate(sorted(summary_data.items()), start=2):
        fill = PatternFill('solid', fgColor=CATEGORY_COLORS.get(cat, 'EAECEE'))
        ws_sum.cell(row=row_idx, column=1, value=cat).fill = fill
        ws_sum.cell(row=row_idx, column=2, value=data['count']).fill = fill
        ws_sum.cell(row=row_idx, column=3, value=round(data['total_debit'], 2)).fill = fill
        ws_sum.cell(row=row_idx, column=4, value=round(data['total_credit'], 2)).fill = fill

    for col_idx, width in enumerate([28, 20, 20, 20], start=1):
        ws_sum.column_dimensions[get_column_letter(col_idx)].width = width

    # Save to bytes
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def export_to_csv(account_details: dict, transactions: list) -> bytes:
    """
    Generate a CSV with account details header + transaction rows.
    Returns bytes (UTF-8 with BOM for Excel compatibility).
    """
    buf = io.StringIO()
    writer = csv.writer(buf)

    # Account details block
    writer.writerow(['=== ACCOUNT DETAILS ==='])
    for key, val in account_details.items():
        writer.writerow([key.replace('_', ' ').title(), val])
    writer.writerow([])

    # Transactions block
    writer.writerow(['=== TRANSACTIONS ==='])
    writer.writerow(COLUMNS)
    for txn in transactions:
        writer.writerow(_row_from_txn(txn))

    # UTF-8 BOM so Excel opens correctly
    return ('\ufeff' + buf.getvalue()).encode('utf-8')

