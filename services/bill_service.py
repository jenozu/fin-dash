from datetime import date, timedelta
from database.database import get_session
from database.models import Bill, BillPayment
from services.settings_service import get_next_paycheck_date
from config.constants import FREQUENCY_DAYS


def get_all_bills():
    session = get_session()
    try:
        return session.query(Bill).filter(Bill.is_active == True).all()
    finally:
        session.close()


def get_bills_before_paycheck():
    paycheck_date = get_next_paycheck_date()
    today = date.today()
    session = get_session()
    try:
        return (
            session.query(Bill)
            .filter(
                Bill.is_active == True,
                Bill.due_date >= today,
                Bill.due_date <= paycheck_date,
            )
            .order_by(Bill.due_date)
            .all()
        )
    finally:
        session.close()


def get_bills_committed():
    return sum(b.amount for b in get_bills_before_paycheck())


def get_monthly_bills_total():
    bills = get_all_bills()
    total = 0.0
    for bill in bills:
        if bill.frequency == "Weekly":
            total += bill.amount * 4.33
        elif bill.frequency == "Bi-Weekly":
            total += bill.amount * 2.17
        elif bill.frequency == "Monthly":
            total += bill.amount
        elif bill.frequency == "Quarterly":
            total += bill.amount / 3.0
        elif bill.frequency == "Annual":
            total += bill.amount / 12.0
    return total


def add_bill(bill_name, amount, due_date, frequency, notes=None):
    session = get_session()
    try:
        session.add(Bill(
            bill_name=bill_name, amount=amount, due_date=due_date,
            frequency=frequency, notes=notes,
        ))
        session.commit()
    finally:
        session.close()


def delete_bill(bill_id):
    session = get_session()
    try:
        session.query(Bill).filter(Bill.id == bill_id).delete()
        session.commit()
    finally:
        session.close()


def mark_bill_paid(bill_id, paid_date=None, amount=None):
    """Record a payment for a bill, then advance its due date by one frequency cycle."""
    paid_date = paid_date or date.today()
    session = get_session()
    try:
        bill = session.query(Bill).filter(Bill.id == bill_id).first()
        if not bill:
            return
        paid_amount = amount if amount is not None else bill.amount
        session.add(BillPayment(
            bill_id=bill.id, amount=paid_amount, paid_date=paid_date, due_date=bill.due_date,
        ))
        days = FREQUENCY_DAYS.get(bill.frequency, 30)
        bill.due_date = bill.due_date + timedelta(days=days)
        session.commit()
    finally:
        session.close()


def get_payment_history(bill_id):
    session = get_session()
    try:
        return (
            session.query(BillPayment)
            .filter(BillPayment.bill_id == bill_id)
            .order_by(BillPayment.paid_date.desc())
            .all()
        )
    finally:
        session.close()


def get_funding_status(bill, account_balance):
    """Compute funding status: Funded, Partially Funded, Scheduled, or Unfunded."""
    paycheck_date = get_next_paycheck_date()
    if bill.due_date is None or bill.due_date > paycheck_date:
        return "Scheduled"
    if account_balance >= bill.amount:
        return "Funded"
    if account_balance > 0:
        return "Partially Funded"
    return "Unfunded"
