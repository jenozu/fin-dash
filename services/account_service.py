from datetime import date
from database.database import get_session
from database.models import Account, AccountSnapshot


def get_all_accounts():
    session = get_session()
    try:
        return session.query(Account).filter(Account.is_active == True).all()
    finally:
        session.close()


def get_spending_account():
    session = get_session()
    try:
        acct = session.query(Account).filter(
            Account.account_role == "Spending",
            Account.is_active == True,
        ).first()
        if acct is None:
            acct = session.query(Account).filter(Account.is_active == True).first()
        return acct
    finally:
        session.close()


def get_spending_balance():
    acct = get_spending_account()
    return acct.current_balance if acct else 0.0


def update_balance(account_id, new_balance):
    session = get_session()
    try:
        acct = session.query(Account).filter(Account.id == account_id).first()
        if acct:
            acct.current_balance = new_balance
            acct.available_balance = new_balance
            session.add(AccountSnapshot(
                account_id=account_id,
                balance=new_balance,
                snapshot_date=date.today(),
            ))
            session.commit()
    finally:
        session.close()


def add_account(account_name, account_type, account_role, institution_name="", balance=0.0, subtype="personal"):
    session = get_session()
    try:
        acct = Account(
            account_name=account_name,
            account_type=account_type,
            account_subtype=subtype,
            account_role=account_role,
            current_balance=balance,
            available_balance=balance,
            institution_name=institution_name or None,
            is_active=True,
        )
        session.add(acct)
        session.flush()
        session.add(AccountSnapshot(account_id=acct.id, balance=balance, snapshot_date=date.today()))
        session.commit()
    finally:
        session.close()


def update_account_details(account_id, account_name, account_role, institution_name):
    session = get_session()
    try:
        acct = session.query(Account).filter(Account.id == account_id).first()
        if acct:
            acct.account_name = account_name
            acct.account_role = account_role
            acct.institution_name = institution_name or None
            session.commit()
    finally:
        session.close()


def deactivate_account(account_id):
    session = get_session()
    try:
        acct = session.query(Account).filter(Account.id == account_id).first()
        if acct:
            acct.is_active = False
            session.commit()
    finally:
        session.close()


def get_balance_history(account_id):
    session = get_session()
    try:
        snaps = (
            session.query(AccountSnapshot)
            .filter(AccountSnapshot.account_id == account_id)
            .order_by(AccountSnapshot.snapshot_date)
            .all()
        )
        return [{"date": s.snapshot_date, "balance": s.balance} for s in snaps]
    finally:
        session.close()
