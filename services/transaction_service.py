from datetime import date, timedelta
from database.database import get_session
from database.models import Transaction
import pandas as pd


def get_transactions_df(days=30, account_id=None):
    session = get_session()
    try:
        cutoff = date.today() - timedelta(days=days)
        q = (
            session.query(Transaction)
            .filter(Transaction.transaction_date >= cutoff)
        )
        if account_id is not None:
            q = q.filter(Transaction.account_id == account_id)
        txns = q.order_by(Transaction.transaction_date.desc()).all()
        data = [{
            "id": t.id,
            "Date": t.transaction_date,
            "Merchant": t.merchant,
            "Category": t.category or "",
            "Amount": t.amount,
            "Notes": t.notes or "",
            "Account": t.account_id,
            "Pending": t.is_pending,
        } for t in txns]
        if not data:
            return pd.DataFrame(columns=["id", "Date", "Merchant", "Category", "Amount", "Notes", "Account", "Pending"])
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


def add_transaction(merchant, amount, category, txn_date, account_id=None, notes=None):
    session = get_session()
    try:
        session.add(Transaction(
            merchant=merchant,
            amount=amount,
            category=category,
            transaction_date=txn_date,
            account_id=account_id,
            notes=notes,
            is_pending=False,
        ))
        session.commit()
    finally:
        session.close()


def update_transaction(txn_id, merchant, amount, category, txn_date, notes=None):
    session = get_session()
    try:
        txn = session.query(Transaction).filter(Transaction.id == txn_id).first()
        if txn:
            txn.merchant = merchant
            txn.amount = amount
            txn.category = category
            txn.transaction_date = txn_date
            txn.notes = notes
            session.commit()
    finally:
        session.close()


def delete_transaction(txn_id):
    session = get_session()
    try:
        session.query(Transaction).filter(Transaction.id == txn_id).delete()
        session.commit()
    finally:
        session.close()


def upsert_plaid_transactions(added: list, modified: list, removed: list) -> dict:
    """
    Sync Plaid transaction deltas into the DB.
    - added: insert if plaid_transaction_id not already in DB
    - modified: update matching plaid_transaction_id rows
    - removed: delete by plaid_transaction_id
    Manual transactions (plaid_transaction_id IS NULL) are never touched.
    Returns {inserted, updated, deleted} counts.
    """
    from services.plaid_service import map_category
    from database.models import Account
    session = get_session()
    inserted = updated = deleted = 0
    try:
        # Build plaid_account_id → db account_id lookup
        accts = session.query(Account).filter(Account.plaid_account_id.isnot(None)).all()
        plaid_to_db = {a.plaid_account_id: a.id for a in accts}

        for pt in added:
            pid = pt.get("transaction_id", "")
            if not pid:
                continue
            exists = session.query(Transaction).filter(Transaction.plaid_transaction_id == pid).first()
            if exists:
                continue
            # Plaid amounts: positive = debit from account (expense), negative = credit (income)
            # We store expenses as negative, income as positive — so negate
            amount = -(pt.get("amount") or 0.0)
            txn_date_raw = pt.get("authorized_date") or pt.get("date")
            try:
                txn_date = date.fromisoformat(txn_date_raw)
            except (TypeError, ValueError):
                continue
            db_acct_id = plaid_to_db.get(pt.get("account_id", ""))
            session.add(Transaction(
                plaid_transaction_id=pid,
                account_id=db_acct_id,
                merchant=pt.get("merchant_name") or pt.get("name") or "Unknown",
                amount=amount,
                category=map_category(pt),
                transaction_date=txn_date,
                is_pending=pt.get("pending", False),
            ))
            inserted += 1

        for pt in modified:
            pid = pt.get("transaction_id", "")
            if not pid:
                continue
            existing = session.query(Transaction).filter(Transaction.plaid_transaction_id == pid).first()
            if not existing:
                continue
            amount = -(pt.get("amount") or 0.0)
            txn_date_raw = pt.get("authorized_date") or pt.get("date")
            try:
                existing.transaction_date = date.fromisoformat(txn_date_raw)
            except (TypeError, ValueError):
                pass
            existing.merchant = pt.get("merchant_name") or pt.get("name") or existing.merchant
            existing.amount = amount
            existing.category = map_category(pt)
            existing.is_pending = pt.get("pending", False)
            updated += 1

        for pt in removed:
            pid = pt.get("transaction_id", "")
            if not pid:
                continue
            session.query(Transaction).filter(Transaction.plaid_transaction_id == pid).delete()
            deleted += 1

        session.commit()
        return {"inserted": inserted, "updated": updated, "deleted": deleted}
    finally:
        session.close()
