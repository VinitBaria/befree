"""
Rule-Based Transaction Classifier.
Categorizes transactions using straightforward keyword matching.
"""
import re

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


def classify_transaction(description: str) -> str:
    """Classify a single transaction description into a category."""
    if not description:
        return "Other"

    text = str(description).lower().strip()

    for category, keywords in CATEGORIES.items():
        for kw in keywords:
            # Word boundary check for short abbreviations (<= 3 chars)
            if len(kw) <= 3:
                if re.search(r'\b' + re.escape(kw) + r'\b', text):
                    return category
            elif kw in text:
                return category

    return "Other"


def classify_all(transactions: list) -> list:
    """Classify a list of transactions in-place."""
    for t in transactions:
        t["category"] = classify_transaction(t.get("description", ""))
    return transactions
