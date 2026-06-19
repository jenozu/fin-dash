from datetime import date
from database.database import get_session
from database.models import Bill
from services.settings_service import get_next_paycheck_date


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
