import streamlit as st
from datetime import date
from database.database import get_session
from database.models import WishlistItem, WishlistDeposit
from config.constants import WISHLIST_STATUSES, PRIORITY_LEVELS
from services.wishlist_service import (
    get_active_wishlist,
    per_paycheck_for_item,
    update_wishlist_item,
    deposit_to_wishlist_item,
    get_wishlist_deposit_history,
)
from services.settings_service import get_pay_frequency

if "editing_wish_id" not in st.session_state:
    st.session_state["editing_wish_id"] = None
if "depositing_wish_id" not in st.session_state:
    st.session_state["depositing_wish_id"] = None

st.header("Wishlist")

today = date.today()
pay_freq = get_pay_frequency()
items = sorted(get_active_wishlist(), key=lambda i: (i.planned_purchase_date or date.max))

if items:
    total_cost = sum(i.estimated_cost for i in items)
    total_saved = sum(i.current_saved for i in items)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Cost", f"${total_cost:,.2f}")
    c2.metric("Total Saved", f"${total_saved:,.2f}")
    c3.metric("Remaining", f"${total_cost - total_saved:,.2f}")
    c4.metric("Items", len(items))

    st.markdown("---")

    for item in items:
        remaining = max(item.estimated_cost - item.current_saved, 0.0)
        pct = min(item.current_saved / item.estimated_cost, 1.0) if item.estimated_cost else 0
        per_check = per_paycheck_for_item(item, pay_freq)
        editing = st.session_state["editing_wish_id"] == item.id
        depositing = st.session_state["depositing_wish_id"] == item.id

        priority_colors = {"High": "#e74c3c", "Medium": "#f39c12", "Low": "#95a5a6"}
        if item.current_saved >= item.estimated_cost:
            badge_text = "Ready"
            badge_color = "#2ecc71"
        elif item.planned_purchase_date and item.planned_purchase_date < today:
            badge_text = "Past Due"
            badge_color = "#e74c3c"
        else:
            badge_text = f"{item.priority} • {item.status}"
            badge_color = priority_colors.get(item.priority, "#95a5a6")

        with st.container(border=True):
            r1a, r1b = st.columns([5, 2])
            badge_html = (
                f" &nbsp;<span style='background:{badge_color};color:#fff;"
                f"padding:2px 8px;border-radius:10px;font-size:0.78em'>{badge_text}</span>"
            )
            r1a.markdown(f"**{item.item_name}**{badge_html}", unsafe_allow_html=True)
            if per_check > 0:
                r1b.markdown(
                    f"<div style='text-align:right;color:#f39c12'>"
                    f"${per_check:,.2f}/paycheck needed</div>",
                    unsafe_allow_html=True,
                )

            st.write(
                f"${item.current_saved:,.2f} / ${item.estimated_cost:,.2f}"
                f"  —  ${remaining:,.2f} remaining"
            )
            st.progress(pct)

            if item.planned_purchase_date:
                days_left = (item.planned_purchase_date - today).days
                if days_left < 0:
                    st.caption(f"Target: {item.planned_purchase_date}  ⚠️ past due by {abs(days_left)} days")
                else:
                    st.caption(f"Target: {item.planned_purchase_date}  ({days_left} days)")
            if item.notes:
                st.caption(item.notes)

            _, btn_dep, btn_edit, btn_del = st.columns([4, 2, 2, 1])

            if btn_dep.button(
                "Cancel" if depositing else "Deposit",
                key=f"dep_btn_w_{item.id}",
            ):
                st.session_state["depositing_wish_id"] = None if depositing else item.id
                if not depositing:
                    st.session_state["editing_wish_id"] = None
                st.rerun()

            if btn_edit.button(
                "Cancel Edit" if editing else "Edit",
                key=f"edit_btn_w_{item.id}",
            ):
                st.session_state["editing_wish_id"] = None if editing else item.id
                if not editing:
                    st.session_state["depositing_wish_id"] = None
                st.rerun()

            if btn_del.button("✕", key=f"del_wish_{item.id}"):
                session = get_session()
                try:
                    session.query(WishlistDeposit).filter(WishlistDeposit.item_id == item.id).delete()
                    session.query(WishlistItem).filter(WishlistItem.id == item.id).delete()
                    session.commit()
                finally:
                    session.close()
                if st.session_state["editing_wish_id"] == item.id:
                    st.session_state["editing_wish_id"] = None
                if st.session_state["depositing_wish_id"] == item.id:
                    st.session_state["depositing_wish_id"] = None
                st.rerun()

            if depositing:
                with st.form(f"deposit_form_w_{item.id}"):
                    dep_amount = st.number_input(
                        "Deposit Amount ($)", min_value=0.01, step=10.0, format="%.2f",
                    )
                    dep_notes = st.text_input("Notes (optional)")
                    ds, dc = st.columns(2)
                    dep_saved = ds.form_submit_button("Add Deposit")
                    dep_cancel = dc.form_submit_button("Cancel")
                    if dep_saved:
                        if dep_amount > 0:
                            deposit_to_wishlist_item(item.id, dep_amount, dep_notes)
                            st.session_state["depositing_wish_id"] = None
                            st.rerun()
                        else:
                            st.warning("Enter an amount greater than $0.")
                    if dep_cancel:
                        st.session_state["depositing_wish_id"] = None
                        st.rerun()

            if editing:
                with st.form(f"edit_form_w_{item.id}"):
                    ec1, ec2 = st.columns(2)
                    new_name = ec1.text_input("Item Name", value=item.item_name)
                    new_cost = ec1.number_input(
                        "Estimated Cost ($)", min_value=0.0,
                        value=float(item.estimated_cost), step=10.0,
                    )
                    new_saved = ec1.number_input(
                        "Current Saved ($)", min_value=0.0,
                        value=float(item.current_saved), step=10.0,
                    )
                    p_idx = PRIORITY_LEVELS.index(item.priority) if item.priority in PRIORITY_LEVELS else 1
                    new_priority = ec2.selectbox("Priority", PRIORITY_LEVELS, index=p_idx)
                    s_idx = WISHLIST_STATUSES.index(item.status) if item.status in WISHLIST_STATUSES else 1
                    new_status = ec2.selectbox("Status", WISHLIST_STATUSES, index=s_idx)
                    new_date = ec2.date_input(
                        "Planned Purchase Date",
                        value=item.planned_purchase_date or today,
                    )
                    new_notes = st.text_input("Notes", value=item.notes or "")
                    es, ec = st.columns(2)
                    edit_saved = es.form_submit_button("Save Changes")
                    edit_cancel = ec.form_submit_button("Cancel")
                    if edit_saved:
                        if new_name:
                            update_wishlist_item(
                                item.id, new_name, new_cost, new_saved,
                                new_date, new_priority, new_status, new_notes,
                            )
                            st.session_state["editing_wish_id"] = None
                            st.rerun()
                        else:
                            st.warning("Item name is required.")
                    if edit_cancel:
                        st.session_state["editing_wish_id"] = None
                        st.rerun()

            with st.expander("Contribution History"):
                history = get_wishlist_deposit_history(item.id)
                if history:
                    for d in history:
                        note = f" — {d.notes}" if d.notes else ""
                        st.write(f"{d.deposit_date} — +${d.amount:,.2f}{note}")
                else:
                    st.write("No contributions recorded yet. Use Deposit to log savings.")
else:
    st.info("No wishlist items yet. Add your first item below.")

st.markdown("---")
st.subheader("Add Wishlist Item")
with st.form("add_wishlist_form"):
    c_a, c_b = st.columns(2)
    name = c_a.text_input("Item Name")
    cost = c_a.number_input("Estimated Cost ($)", min_value=0.0, step=10.0)
    saved = c_a.number_input("Current Saved ($)", min_value=0.0, step=10.0)
    priority = c_b.selectbox("Priority", PRIORITY_LEVELS, index=1)
    status = c_b.selectbox("Status", WISHLIST_STATUSES, index=1)
    purchase_date = c_b.date_input("Planned Purchase Date")
    notes = st.text_input("Notes (optional)")
    if st.form_submit_button("Add Item") and name:
        session = get_session()
        try:
            session.add(WishlistItem(
                item_name=name, estimated_cost=cost, current_saved=saved,
                planned_purchase_date=purchase_date, priority=priority,
                status=status, notes=notes,
            ))
            session.commit()
        finally:
            session.close()
        st.success(f"Added: {name}")
        st.rerun()
