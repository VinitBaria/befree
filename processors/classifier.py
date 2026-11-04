"""
Simple Rule-Based Transaction Classifier (No ML/LLM dependencies).

Categorizes transactions using direct keyword matching with word-boundary
protection for short terms (e.g. 'atm', 'emi', 'lic').
"""
import re

# Category -> List of matching keywords
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


def _match(text: str, kw: str) -> bool:
    """Check if keyword matches in text (uses word boundary for short abbreviations)."""
    if len(kw) <= 3:
        return bool(re.search(r'\b' + re.escape(kw) + r'\b', text))
    return kw in text


def classify_transaction(description: str) -> dict:
    """
    Classify a single transaction by matching keywords against description.
    Returns: { 'category': str, 'confidence': float, 'method': 'rule' }
    """
    if not description:
        return {"category": "Other", "confidence": 0.0, "method": "rule"}

    text = str(description).lower().strip()

    for category, keywords in CATEGORIES.items():
        if any(_match(text, kw) for kw in keywords):
            return {"category": category, "confidence": 0.95, "method": "rule"}

    return {"category": "Other", "confidence": 0.50, "method": "rule"}


def classify_all(transactions: list) -> list:
    """Classify a list of transactions in-place."""
    for t in transactions:
        res = classify_transaction(t.get("description", ""))
        t["category"] = res["category"]
        t["confidence"] = res["confidence"]
        t["classification_method"] = res["method"]
    return transactions
