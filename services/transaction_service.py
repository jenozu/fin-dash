from datetime import date, timedelta
from database.database import get_session
from database.models import Transaction
import pandas as pd


def get_transactions_df(days=30, account_id=None):
    session = get_session()
    try:
        cutoff = date.today() - timedelta(days=days)
        q = session.query(Transaction).filter(Transaction.transaction_date >= cutoff)
        if account_id is not None:
            q = q.filter(Transaction.account_id == account_id)
        txns = q.order_by(Transaction.transaction_date.desc()).all()
        cols = ["id", "Date", "Merchant", "Category", "Amount", "Account", "Notes", "Manual"]
        data = [
            {
                "id": t.id,
                "Date": t.transaction_date,
                "Merchant": t.merchant,
                "Category": t.category or "",
                "Amount": t.amount,
                "Account": t.account_id,
                "Notes": t.notes or "",
                "Manual": t.plaid_transaction_id is None,
            }
            for t in txns
        ]
        if not data:
            return pd.DataFrame(columns=cols)
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


def add_transaction(merchant, amount, category, transaction_date, account_id=None, notes=""):
    session = get_session()
    try:
        session.add(Transaction(
            merchant=merchant,
            amount=float(amount),
            category=category,
            transaction_date=transaction_date,
            account_id=account_id,
            notes=notes or "",
            is_pending=False,
        ))
        session.commit()
        return True
    finally:
        session.close()


def update_transaction(txn_id, merchant, amount, category, transaction_date, notes):
    session = get_session()
    try:
        txn = session.query(Transaction).filter(Transaction.id == txn_id).first()
        if not txn:
            return False
        txn.merchant = merchant
        txn.amount = float(amount)
        txn.category = category
        txn.transaction_date = transaction_date
        txn.notes = notes or ""
        session.commit()
        return True
    finally:
        session.close()


def delete_transaction(txn_id):
    session = get_session()
    try:
        session.query(Transaction).filter(Transaction.id == txn_id).delete()
        session.commit()
        return True
    finally:
        session.close()
