import streamlit as st
from datetime import date
from database.database import get_session
from database.models import Bill, BillPayment
from config.constants import BILL_FREQUENCIES
from services.bill_service import (
    get_all_bills,
    get_monthly_bills_total,
    mark_bill_paid,
    update_bill,
    get_bill_payment_history,
    calculate_funding_statuses,
)
from services.allocation_service import get_current_balance
from services.settings_service import get_next_paycheck_date

FUNDING_COLORS = {
    "Funded": "#2ecc71",
    "Partially Funded": "#f39c12",
    "Unfunded": "#e74c3c",
    "Scheduled": "#95a5a6",
}

if "editing_bill_id" not in st.session_state:
    st.session_state["editing_bill_id"] = None

st.header("Bills")

today = date.today()
next_paycheck = get_next_paycheck_date()
balance = get_current_balance()
bills = sorted(get_all_bills(), key=lambda b: b.due_date)

monthly_total = get_monthly_bills_total()
overdue_bills = [b for b in bills if b.due_date and b.due_date < today]
due_in_30 = [b for b in bills if b.due_date and 0 <= (b.due_date - today).days <= 30]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Monthly Obligations", f"${monthly_total:,.2f}")
c2.metric("Active Bills", len(bills))
c3.metric("Due in 30 Days", len(due_in_30))
if overdue_bills:
    c4.metric("Overdue", len(overdue_bills), delta=f"-{len(overdue_bills)}")
else:
    c4.metric("Overdue", 0)

funding_statuses = calculate_funding_statuses(bills, balance, next_paycheck)
st.caption(
    f"Funding based on current balance of ${balance:,.2f} "
    f"| Paycheck window through {next_paycheck}"
)

st.markdown("---")
st.subheader("All Bills")

if bills:
    for bill in bills:
        status = funding_statuses.get(bill.id, "Scheduled")
        color = FUNDING_COLORS[status]
        days_until = (bill.due_date - today).days if bill.due_date else None

        if days_until is not None and days_until < 0:
            due_label = f"⚠️ {bill.due_date} (overdue)"
        elif days_until == 0:
            due_label = f"{bill.due_date} (today)"
        else:
            due_label = str(bill.due_date)

        with st.container(border=True):
            r1a, r1b, r1c, r1d = st.columns([4, 2, 2, 2])
            r1a.markdown(
                f"**{bill.bill_name}** &nbsp;"
                f"<span style='background:{color};color:#fff;padding:2px 8px;"
                f"border-radius:10px;font-size:0.78em'>{status}</span>",
                unsafe_allow_html=True,
            )
            r1b.write(f"${bill.amount:,.2f}")
            r1c.write(due_label)
            r1d.write(bill.frequency)

            editing = st.session_state["editing_bill_id"] == bill.id
            _, r2b, r2c, r2d = st.columns([4, 2, 2, 2])

            if r2b.button("Cancel Edit" if editing else "Edit", key=f"edit_{bill.id}"):
                st.session_state["editing_bill_id"] = None if editing else bill.id
                st.rerun()

            if r2c.button("Mark as Paid", key=f"paid_{bill.id}"):
                mark_bill_paid(bill.id)
                st.rerun()

            if r2d.button("✕", key=f"del_{bill.id}"):
                session = get_session()
                try:
                    session.query(BillPayment).filter(BillPayment.bill_id == bill.id).delete()
                    session.query(Bill).filter(Bill.id == bill.id).delete()
                    session.commit()
                finally:
                    session.close()
                if st.session_state["editing_bill_id"] == bill.id:
                    st.session_state["editing_bill_id"] = None
                st.rerun()

            if editing:
                with st.form(f"edit_form_{bill.id}"):
                    ec1, ec2 = st.columns(2)
                    new_name = ec1.text_input("Bill Name", value=bill.bill_name)
                    new_amount = ec1.number_input(
                        "Amount ($)", min_value=0.0, value=float(bill.amount),
                        step=1.0, format="%.2f",
                    )
                    new_due = ec2.date_input("Due Date", value=bill.due_date)
                    freq_idx = BILL_FREQUENCIES.index(bill.frequency) if bill.frequency in BILL_FREQUENCIES else 2
                    new_freq = ec2.selectbox("Frequency", BILL_FREQUENCIES, index=freq_idx)
                    new_notes = st.text_input("Notes", value=bill.notes or "")
                    sc, cc = st.columns(2)
                    saved = sc.form_submit_button("Save Changes")
                    cancelled = cc.form_submit_button("Cancel")
                    if saved:
                        if new_name:
                            update_bill(bill.id, new_name, new_amount, new_due, new_freq, new_notes)
                            st.session_state["editing_bill_id"] = None
                            st.rerun()
                        else:
                            st.warning("Bill name is required.")
                    if cancelled:
                        st.session_state["editing_bill_id"] = None
                        st.rerun()

            with st.expander("Payment History"):
                history = get_bill_payment_history(bill.id)
                if history:
                    for p in history:
                        note = f" — {p.notes}" if p.notes else ""
                        st.write(f"{p.paid_date} — ${p.amount_paid:,.2f}{note}")
                else:
                    st.write("No payments recorded yet.")
else:
    st.info("No bills yet. Add your first bill below.")

st.markdown("---")
st.subheader("Add Bill")
with st.form("add_bill_form"):
    ca, cb = st.columns(2)
    name = ca.text_input("Bill Name")
    amount = ca.number_input("Amount ($)", min_value=0.0, step=1.0, format="%.2f")
    due_date = cb.date_input("Due Date")
    frequency = cb.selectbox("Frequency", BILL_FREQUENCIES, index=2)
    notes = st.text_input("Notes (optional)")
    if st.form_submit_button("Add Bill") and name:
        session = get_session()
        try:
            session.add(Bill(
                bill_name=name, amount=amount, due_date=due_date,
                frequency=frequency, notes=notes,
            ))
            session.commit()
        finally:
            session.close()
        st.success(f"Added: {name}")
        st.rerun()
