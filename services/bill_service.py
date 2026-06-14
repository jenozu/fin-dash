from calendar import monthrange
from datetime import date, timedelta
from database.database import get_session
from database.models import Bill, BillPayment
from services.settings_service import get_next_paycheck_date


def get_all_bills():
    session = get_session()
    try:
        return session.query(Bill).filter(Bill.is_active == True).all()
    finally:
        session.close()


def get_bills_before_paycheck():
    """Bills due on or before the next paycheck, including any overdue bills."""
    paycheck_date = get_next_paycheck_date()
    session = get_session()
    try:
        return (
            session.query(Bill)
            .filter(
                Bill.is_active == True,
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


def advance_due_date(bill):
    """Return the next due date using calendar-correct month arithmetic."""
    current = bill.due_date
    if bill.frequency == "Weekly":
        return current + timedelta(days=7)
    elif bill.frequency == "Bi-Weekly":
        return current + timedelta(days=14)
    elif bill.frequency == "Monthly":
        month = current.month + 1
        year = current.year
        if month > 12:
            month = 1
            year += 1
        day = min(current.day, monthrange(year, month)[1])
        return date(year, month, day)
    elif bill.frequency == "Quarterly":
        month = current.month + 3
        year = current.year
        if month > 12:
            month -= 12
            year += 1
        day = min(current.day, monthrange(year, month)[1])
        return date(year, month, day)
    elif bill.frequency == "Annual":
        try:
            return current.replace(year=current.year + 1)
        except ValueError:
            return date(current.year + 1, current.month, 28)
    return current + timedelta(days=30)


def mark_bill_paid(bill_id, amount_paid=None):
    """Record payment and advance due date by one period from the current due date."""
    session = get_session()
    try:
        bill = session.query(Bill).filter(Bill.id == bill_id).first()
        if not bill:
            return False
        if amount_paid is None:
            amount_paid = bill.amount
        session.add(BillPayment(
            bill_id=bill_id,
            paid_date=date.today(),
            amount_paid=amount_paid,
        ))
        bill.due_date = advance_due_date(bill)
        session.commit()
        return True
    finally:
        session.close()


def update_bill(bill_id, bill_name, amount, due_date, frequency, notes):
    session = get_session()
    try:
        bill = session.query(Bill).filter(Bill.id == bill_id).first()
        if not bill:
            return False
        bill.bill_name = bill_name
        bill.amount = float(amount)
        bill.due_date = due_date
        bill.frequency = frequency
        bill.notes = notes or ""
        session.commit()
        return True
    finally:
        session.close()


def calculate_funding_statuses(bills, balance, paycheck_date):
    """
    Cascading waterfall sorted by due date.
    Bills due <= paycheck_date: Funded / Partially Funded / Unfunded.
    Bills due > paycheck_date: Scheduled.
    """
    statuses = {}
    remaining = balance
    for bill in sorted(bills, key=lambda b: b.due_date):
        if bill.due_date > paycheck_date:
            statuses[bill.id] = "Scheduled"
        elif remaining >= bill.amount:
            statuses[bill.id] = "Funded"
            remaining -= bill.amount
        elif remaining > 0:
            statuses[bill.id] = "Partially Funded"
            remaining = 0.0
        else:
            statuses[bill.id] = "Unfunded"
    return statuses


def get_bill_payment_history(bill_id, limit=5):
    session = get_session()
    try:
        return (
            session.query(BillPayment)
            .filter(BillPayment.bill_id == bill_id)
            .order_by(BillPayment.paid_date.desc())
            .limit(limit)
            .all()
        )
    finally:
        session.close()
