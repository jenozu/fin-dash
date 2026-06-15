from datetime import date, datetime
from database.database import get_session
from database.models import Account, AccountSnapshot


def get_all_accounts():
    session = get_session()
    try:
        return (
            session.query(Account)
            .filter(Account.is_active == True)
            .order_by(Account.id)
            .all()
        )
    finally:
        session.close()


def get_account_by_role(role):
    session = get_session()
    try:
        return session.query(Account).filter(
            Account.account_role == role,
            Account.is_active == True,
        ).first()
    finally:
        session.close()


def get_spending_account():
    """TAC account. Falls back to first active account if none designated."""
    account = get_account_by_role("Spending")
    if account:
        return account
    session = get_session()
    try:
        return session.query(Account).filter(Account.is_active == True).first()
    finally:
        session.close()


def update_balance(account_id, current_balance, available_balance=None, notes=""):
    """Update balance, record snapshot, update last_synced."""
    session = get_session()
    try:
        account = session.query(Account).filter(Account.id == account_id).first()
        if not account:
            return False
        account.current_balance = float(current_balance)
        account.available_balance = float(
            available_balance if available_balance is not None else current_balance
        )
        account.last_synced = datetime.utcnow()
        session.add(AccountSnapshot(
            account_id=account_id,
            snapshot_date=date.today(),
            balance=float(current_balance),
            notes=notes or "",
        ))
        session.commit()
        return True
    finally:
        session.close()


def add_account(account_name, account_type, account_subtype, account_role,
                institution_name, current_balance, available_balance=None):
    """Create account and record opening balance snapshot."""
    session = get_session()
    try:
        account = Account(
            account_name=account_name,
            account_type=account_type,
            account_subtype=account_subtype or None,
            account_role=account_role or None,
            institution_name=institution_name or "",
            current_balance=float(current_balance),
            available_balance=float(
                available_balance if available_balance is not None else current_balance
            ),
            is_active=True,
        )
        session.add(account)
        session.flush()
        session.add(AccountSnapshot(
            account_id=account.id,
            snapshot_date=date.today(),
            balance=float(current_balance),
            notes="Opening balance",
        ))
        session.commit()
        return account.id
    finally:
        session.close()


def update_account_details(account_id, account_name, account_type, account_subtype,
                           account_role, institution_name):
    session = get_session()
    try:
        account = session.query(Account).filter(Account.id == account_id).first()
        if not account:
            return False
        account.account_name = account_name
        account.account_type = account_type
        account.account_subtype = account_subtype or None
        account.account_role = account_role or None
        account.institution_name = institution_name or ""
        session.commit()
        return True
    finally:
        session.close()


def deactivate_account(account_id):
    """Soft delete — preserves history, hides from active views."""
    session = get_session()
    try:
        account = session.query(Account).filter(Account.id == account_id).first()
        if not account:
            return False
        account.is_active = False
        session.commit()
        return True
    finally:
        session.close()


def get_balance_history(account_id, limit=30):
    """Returns ascending order (oldest first) for chart display."""
    session = get_session()
    try:
        return (
            session.query(AccountSnapshot)
            .filter(AccountSnapshot.account_id == account_id)
            .order_by(AccountSnapshot.snapshot_date.asc(), AccountSnapshot.id.asc())
            .limit(limit)
            .all()
        )
    finally:
        session.close()
