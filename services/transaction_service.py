from datetime import date, timedelta
from database.database import get_session
from database.models import Transaction
import pandas as pd


def get_transactions_df(days=30):
    session = get_session()
    try:
        cutoff = date.today() - timedelta(days=days)
        txns = (
            session.query(Transaction)
            .filter(Transaction.transaction_date >= cutoff)
            .order_by(Transaction.transaction_date.desc())
            .all()
        )
        data = [{
            "Date": t.transaction_date,
            "Merchant": t.merchant,
            "Category": t.category or "",
            "Amount": t.amount,
        } for t in txns]
        if not data:
            return pd.DataFrame(columns=["Date", "Merchant", "Category", "Amount"])
        return pd.DataFrame(data)
    finally:
        session.close()


def get_monthly_spending():
    df = get_transactions_df(30)
    if df.empty:
        return 0.0
    return abs(df[df["Amount"] < 0]["Amount"].sum())


def get_monthly_income():
    df = get_transactions_df(30)
    if df.empty:
        return 0.0
    return float(df[df["Amount"] > 0]["Amount"].sum())


def get_spending_by_category(days=30):
    df = get_transactions_df(days)
    if df.empty:
        return pd.DataFrame(columns=["Category", "Amount"])
    spending = df[df["Amount"] < 0].copy()
    spending["Amount"] = spending["Amount"].abs()
    return (
        spending.groupby("Category")["Amount"]
        .sum()
        .reset_index()
        .sort_values("Amount", ascending=False)
    )
