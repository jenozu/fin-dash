import streamlit as st
from datetime import date
from database.database import get_session
from database.models import WishlistItem
from config.constants import WISHLIST_STATUSES, PRIORITY_LEVELS
from services.wishlist_service import per_paycheck_for_item
from services.settings_service import get_pay_frequency

st.header("Wishlist")

session = get_session()
try:
    items = (
        session.query(WishlistItem)
        .filter(WishlistItem.status.notin_(["Purchased", "Cancelled"]))
        .order_by(WishlistItem.planned_purchase_date)
        .all()
    )
    pay_freq = get_pay_frequency()

    if items:
        total_cost = sum(i.estimated_cost for i in items)
        total_saved = sum(i.current_saved for i in items)

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Cost", f"${total_cost:,.2f}")
        c2.metric("Total Saved", f"${total_saved:,.2f}")
        c3.metric("Remaining", f"${total_cost - total_saved:,.2f}")

        st.markdown("---")

        for item in items:
            remaining = item.estimated_cost - item.current_saved
            pct = min(item.current_saved / item.estimated_cost, 1.0) if item.estimated_cost else 0
            per_check = per_paycheck_for_item(item, pay_freq)

            with st.container(border=True):
                c_n, c_p, c_m, c_x = st.columns([3, 3, 2, 1])
                with c_n:
                    st.subheader(item.item_name)
                    st.caption(f"{item.priority} priority — {item.status}")
                    if item.notes:
                        st.caption(item.notes)
                with c_p:
                    st.write(f"${item.current_saved:,.2f} / ${item.estimated_cost:,.2f}")
                    st.progress(pct)
                    st.caption(f"${remaining:,.2f} remaining")
                with c_m:
                    if item.planned_purchase_date:
                        days_left = (item.planned_purchase_date - date.today()).days
                        st.write(f"By: {item.planned_purchase_date}")
                        st.write(f"{days_left} days left")
                    st.write(f"${per_check:,.2f}/paycheck")
                if c_x.button("X", key=f"del_wish_{item.id}"):
                    session.query(WishlistItem).filter(WishlistItem.id == item.id).delete()
                    session.commit()
                    st.rerun()
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
            session.add(WishlistItem(
                item_name=name, estimated_cost=cost, current_saved=saved,
                planned_purchase_date=purchase_date, priority=priority,
                status=status, notes=notes,
            ))
            session.commit()
            st.success(f"Added: {name}")
            st.rerun()
finally:
    session.close()
