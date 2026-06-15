BILL_FREQUENCIES = ["Weekly", "Bi-Weekly", "Monthly", "Quarterly", "Annual"]
PAY_FREQUENCIES = ["Weekly", "Bi-Weekly", "Semi-Monthly", "Monthly"]
WISHLIST_STATUSES = ["Idea", "Planning", "Saving", "Ready To Buy", "Purchased", "Cancelled"]
PRIORITY_LEVELS = ["Low", "Medium", "High"]

FREQUENCY_DAYS = {
    "Weekly": 7,
    "Bi-Weekly": 14,
    "Monthly": 30,
    "Quarterly": 91,
    "Annual": 365,
}

PAY_PERIODS_PER_YEAR = {
    "Weekly": 52,
    "Bi-Weekly": 26,
    "Semi-Monthly": 24,
    "Monthly": 12,
}

ACCOUNT_ROLES = ["Spending", "Bills Reserve", "Savings", "General"]
ACCOUNT_TYPES = ["depository", "credit", "loan", "investment", "other"]
ACCOUNT_SUBTYPES = [
    "checking", "savings", "money market", "cd",
    "credit card", "mortgage", "auto loan", "student loan",
    "brokerage", "other",
]
TRANSACTION_CATEGORIES = [
    "Income", "Groceries", "Gas", "Dining", "Coffee", "Shopping",
    "Subscriptions", "Entertainment", "Health", "Home", "Transfer",
    "Bills", "Other",
]
