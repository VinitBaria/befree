"""
Bank Statement Processor — Befree
Flask app: UI served from templates/index.html, API endpoints below.
Run:  python app.py
Open: http://localhost:5000
"""
import os, sys, uuid, io, tempfile, traceback
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from processors.pdf_detector   import detect_pdf_type
from processors.text_extractor import extract_from_text_pdf
from processors.image_extractor import extract_from_image_pdf
from processors.classifier      import classify_all
from exporters.exporter         import export_to_excel, export_to_csv

app  = Flask(__name__)
CORS(app)

# In-memory session store (demo only)
_sessions: dict = {}


@app.route('/')
def index():
    return render_template('index.html')


# ─────────────────────────────────────────────────────────────────────────────
# API endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'})


@app.route('/api/process', methods=['POST'])
def process_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    f = request.files['file']
    if not f.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Only PDF files accepted'}), 400

    sid = str(uuid.uuid4())
    tmp = os.path.join(tempfile.gettempdir(), f'stmt_{sid}.pdf')
    try:
        f.save(tmp)
        pdf_type = detect_pdf_type(tmp)
        result   = extract_from_image_pdf(tmp) if pdf_type == 'image' else extract_from_text_pdf(tmp)
        txns     = classify_all(result.get('transactions', []))
        acc      = result.get('account_details', {})
        _sessions[sid] = {'account_details': acc, 'transactions': txns}

        return jsonify({
            'session_id': sid,
            'pdf_type':   pdf_type,
            'extraction_method': result.get('extraction_method'),
            'account_details':   acc,
            'transactions':      txns,
            'summary': _build_summary(txns),
            'error': result.get('error'),
        })
    except Exception as e:
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500
    finally:
        try: os.remove(tmp)
        except: pass


@app.route('/api/demo')
def demo():
    txns = classify_all([
        {'date':'2024-01-03','description':'UPI/9876543210/PhonePe/FOOD ORDER',          'debit':450,    'credit':None,   'balance':24550,  'reference':'UPI123'},
        {'date':'2024-01-05','description':'Salary credit PAYROLL/EMP001/JAN2024',        'debit':None,   'credit':55000,  'balance':79550,  'reference':'NEFT01'},
        {'date':'2024-01-07','description':'ATM WDL 123456 HDFC ATM MUMBAI',              'debit':5000,   'credit':None,   'balance':74550,  'reference':''},
        {'date':'2024-01-08','description':'Amazon.in purchase order #AMZ456789',          'debit':1299,   'credit':None,   'balance':73251,  'reference':'AMZ456'},
        {'date':'2024-01-10','description':'BESCOM electricity bill payment JAN',          'debit':1850,   'credit':None,   'balance':71401,  'reference':''},
        {'date':'2024-01-12','description':'EMI debit housing loan HDFC/HL2024',           'debit':18500,  'credit':None,   'balance':52901,  'reference':'EMI01'},
        {'date':'2024-01-14','description':'Swiggy food order dinner #SW789',              'debit':340,    'credit':None,   'balance':52561,  'reference':''},
        {'date':'2024-01-15','description':'Netflix subscription monthly renewal',         'debit':649,    'credit':None,   'balance':51912,  'reference':''},
        {'date':'2024-01-18','description':'LIC premium payment policy #LIC1234',          'debit':3200,   'credit':None,   'balance':48712,  'reference':''},
        {'date':'2024-01-19','description':'NEFT inward transfer RAHUL/HDFC',              'debit':None,   'credit':10000,  'balance':58712,  'reference':'NEFT02'},
        {'date':'2024-01-20','description':'Refund Amazon order returned #RFD123',         'debit':None,   'credit':1299,   'balance':60011,  'reference':'RFD123'},
        {'date':'2024-01-22','description':'HPCL petrol pump fuel fill #HP234',            'debit':2000,   'credit':None,   'balance':58011,  'reference':''},
        {'date':'2024-01-25','description':'SIP debit Groww mutual fund Jan24',            'debit':5000,   'credit':None,   'balance':53011,  'reference':'SIP01'},
        {'date':'2024-01-26','description':'Mobile recharge Jio postpaid #JIO456',         'debit':399,    'credit':None,   'balance':52612,  'reference':''},
        {'date':'2024-01-27','description':'IRCTC train ticket booking TKT789',            'debit':1200,   'credit':None,   'balance':51412,  'reference':''},
        {'date':'2024-01-28','description':'OYO hotel booking Bangalore stay',             'debit':2500,   'credit':None,   'balance':48912,  'reference':''},
        {'date':'2024-01-29','description':'Apollo pharmacy medicine bill',                'debit':890,    'credit':None,   'balance':48022,  'reference':''},
        {'date':'2024-01-30','description':'Annual fee service charge GST',                'debit':590,    'credit':None,   'balance':47432,  'reference':''},
        {'date':'2024-01-31','description':'FASTag toll recharge NHAI/TAG001',             'debit':500,    'credit':None,   'balance':46932,  'reference':''},
    ])
    acc = {
        'account_holder':   'Rahul Sharma',
        'account_number':   '1234 5678 9012',
        'bank_name':        'HDFC Bank',
        'ifsc':             'HDFC0001234',
        'statement_period': '01/01/2024 to 31/01/2024',
    }
    sid = 'demo-' + uuid.uuid4().hex[:8]
    _sessions[sid] = {'account_details': acc, 'transactions': txns}
    return jsonify({
        'session_id': sid,
        'pdf_type': 'demo',
        'account_details': acc,
        'transactions': txns,
        'summary': _build_summary(txns),
    })


@app.route('/api/export/<sid>/<fmt>')
def export(sid, fmt):
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
    return jsonify({'error': 'Use excel or csv'}), 400


def _build_summary(txns):
    cats = {}
    for t in txns:
        c = t.get('category', 'Other')
        cats[c] = cats.get(c, 0) + 1
    return {
        'total_transactions': len(txns),
        'total_debit':  round(sum(t.get('debit')  or 0 for t in txns), 2),
        'total_credit': round(sum(t.get('credit') or 0 for t in txns), 2),
        'category_breakdown': cats,
    }


if __name__ == '__main__':
    print("\n  Bank Statement Processor — Befree")
    print("  Open in browser: http://localhost:5000\n")
    app.run(debug=True, port=5000)
