"""
Simplified Non-LLM Transaction Classifier.

Approach:
1. Heuristic Rule-Based Matching (Direct keyword matching with word boundaries for short terms)
2. Traditional Machine Learning (CountVectorizer + Naive Bayes Classifier)
"""

import re
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline

# ── Category Dictionary ───────────────────────────────────────────────────────
CATEGORIES = {
    "UPI Transfer":               ["upi", "bhim", "gpay", "phonepe", "paytm"],
    "NEFT / RTGS Transfer":       ["neft", "rtgs", "imps", "fund transfer"],
    "ATM Withdrawal":             ["atm", "cash withdrawal", "atm wdl", "wdl"],
    "Salary / Income":            ["salary", "payroll", "wages", "stipend"],
    "EMI / Loan Payment":         ["emi", "loan", "repayment", "nach/emi"],
    "Utility Bills":              ["electricity", "bescom", "msedcl", "water bill", "gas bill", "broadband"],
    "Mobile / Recharge":          ["recharge", "airtel", "jio", "vodafone", "bsnl"],
    "Insurance":                  ["insurance", "lic", "premium", "policy"],
    "Investments / Mutual Funds": ["mutual fund", "sip", "groww", "zerodha", "nps", "ppf", "etf"],
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

# ── Train Traditional ML Model directly on Category Vocabulary ──────────────
_X = [keyword for cat, kws in CATEGORIES.items() for keyword in kws]
_y = [cat for cat, kws in CATEGORIES.items() for keyword in kws]

# Simple 2-stage ML pipeline: Bag-of-Words + Multinomial Naive Bayes
_model = make_pipeline(
    CountVectorizer(ngram_range=(1, 2)),
    MultinomialNB(fit_prior=False)
)
_model.fit(_X, _y)


def _matches_keyword(text: str, kw: str) -> bool:
    """Check if kw is in text, using boundary for short abbreviations."""
    if len(kw) <= 3:
        return bool(re.search(r'\b' + re.escape(kw) + r'\b', text))
    return kw in text


# ── Public Classification Interface ──────────────────────────────────────────
def classify_transaction(description: str) -> dict:
    """
    Classify a transaction using Rule-Based matching first, then ML model fallback.
    Returns: { 'category': str, 'confidence': float, 'method': 'heuristic' | 'ml' }
    """
    if not description or not str(description).strip():
        return {"category": "Other", "confidence": 0.0, "method": "heuristic"}

    text = str(description).lower().strip()

    # Step 1: Heuristic rule-based check
    for cat, keywords in CATEGORIES.items():
        if any(_matches_keyword(text, kw) for kw in keywords):
            return {"category": cat, "confidence": 0.95, "method": "heuristic"}

    # Step 2: Traditional ML fallback
    try:
        predicted_cat = str(_model.predict([text])[0])
        prob = max(_model.predict_proba([text])[0])
        return {"category": predicted_cat, "confidence": round(float(prob), 2), "method": "ml"}
    except Exception:
        return {"category": "Other", "confidence": 0.30, "method": "heuristic"}


def classify_all(transactions: list) -> list:
    """Classify a list of transactions in-place."""
    for t in transactions:
        res = classify_transaction(t.get("description", ""))
        t["category"] = res["category"]
        t["confidence"] = res["confidence"]
        t["classification_method"] = res["method"]
    return transactions
