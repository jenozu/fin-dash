import streamlit as st
from datetime import date
from database.database import get_session
from database.models import Bill
from config.constants import BILL_FREQUENCIES

st.header("Bills")

session = get_session()
try:
    bills = session.query(Bill).filter(Bill.is_active == True).order_by(Bill.due_date).all()
    today = date.today()

    monthly_total = 0.0
    for b in bills:
        if b.frequency == "Weekly":
            monthly_total += b.amount * 4.33
        elif b.frequency == "Bi-Weekly":
            monthly_total += b.amount * 2.17
        elif b.frequency == "Monthly":
            monthly_total += b.amount
        elif b.frequency == "Quarterly":
            monthly_total += b.amount / 3.0
        elif b.frequency == "Annual":
            monthly_total += b.amount / 12.0

    upcoming_30 = [b for b in bills if b.due_date and (b.due_date - today).days <= 30]

    c1, c2, c3 = st.columns(3)
    c1.metric("Monthly Obligations", f"${monthly_total:,.2f}")
    c2.metric("Active Bills", len(bills))
    c3.metric("Due in 30 Days", len(upcoming_30))

    st.markdown("---")
    st.subheader("All Bills")

    if bills:
        for bill in bills:
            days_until = (bill.due_date - today).days if bill.due_date else None
            label = bill.bill_name
            if days_until is not None:
                if days_until < 0:
                    label += " (overdue)"
                elif days_until <= 7:
                    label += " (due soon)"

            with st.container(border=True):
                c_n, c_a, c_d, c_f, c_x = st.columns([3, 2, 2, 2, 1])
                c_n.write(f"**{label}**")
                c_a.write(f"${bill.amount:,.2f}")
                c_d.write(str(bill.due_date))
                c_f.write(bill.frequency)
                if c_x.button("X", key=f"del_bill_{bill.id}"):
                    session.query(Bill).filter(Bill.id == bill.id).delete()
                    session.commit()
                    st.rerun()
    else:
        st.info("No bills yet. Add your first bill below.")

    st.markdown("---")
    st.subheader("Add Bill")
    with st.form("add_bill_form"):
        c_a, c_b = st.columns(2)
        name = c_a.text_input("Bill Name")
        amount = c_a.number_input("Amount ($)", min_value=0.0, step=1.0, format="%.2f")
        due_date = c_b.date_input("Due Date")
        frequency = c_b.selectbox("Frequency", BILL_FREQUENCIES, index=2)
        notes = st.text_input("Notes (optional)")
        if st.form_submit_button("Add Bill") and name:
            session.add(Bill(
                bill_name=name, amount=amount, due_date=due_date,
                frequency=frequency, notes=notes,
            ))
            session.commit()
            st.success(f"Added: {name}")
            st.rerun()
finally:
    session.close()
