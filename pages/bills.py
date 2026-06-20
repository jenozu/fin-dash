import streamlit as st
from datetime import date
from config.constants import BILL_FREQUENCIES
from services.bill_service import (
    get_all_bills, get_monthly_bills_total, add_bill, delete_bill,
    mark_bill_paid, get_payment_history, get_funding_status,
)
from services.account_service import get_spending_balance

st.header("Bills")

bills = get_all_bills()
today = date.today()

monthly_total = get_monthly_bills_total()
upcoming_30 = [b for b in bills if b.due_date and 0 <= (b.due_date - today).days <= 30]
spending_balance = get_spending_balance()

c1, c2, c3 = st.columns(3)
c1.metric("Monthly Obligations", f"${monthly_total:,.2f}")
c2.metric("Active Bills", len(bills))
c3.metric("Due in 30 Days", len(upcoming_30))

st.markdown("---")
st.subheader("All Bills")

FUNDING_BADGE = {
    "Funded": "🟢 Funded",
    "Partially Funded": "🟡 Partially Funded",
    "Scheduled": "🔵 Scheduled",
    "Unfunded": "🔴 Unfunded",
}

if bills:
    for bill in sorted(bills, key=lambda b: b.due_date or date.max):
        days_until = (bill.due_date - today).days if bill.due_date else None
        label = bill.bill_name
        if days_until is not None:
            if days_until < 0:
                label += " (overdue)"
            elif days_until <= 7:
                label += " (due soon)"
        status = get_funding_status(bill, spending_balance)

        with st.container(border=True):
            c_n, c_a, c_d, c_f, c_s, c_p, c_x = st.columns([3, 2, 2, 2, 2, 1, 1])
            c_n.write(f"**{label}**")
            c_a.write(f"${bill.amount:,.2f}")
            c_d.write(str(bill.due_date))
            c_f.write(bill.frequency)
            c_s.write(FUNDING_BADGE.get(status, status))
            if c_p.button("Mark Paid", key=f"pay_bill_{bill.id}"):
                mark_bill_paid(bill.id)
                st.success(f"Marked {bill.bill_name} as paid.")
                st.rerun()
            if c_x.button("X", key=f"del_bill_{bill.id}"):
                delete_bill(bill.id)
                st.rerun()

            history = get_payment_history(bill.id)
            if history:
                with st.expander(f"Payment history ({len(history)})"):
                    for payment in history:
                        st.write(f"Paid ${payment.amount:,.2f} on {payment.paid_date} (was due {payment.due_date})")
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
        add_bill(name, amount, due_date, frequency, notes or None)
        st.success(f"Added: {name}")
        st.rerun()
