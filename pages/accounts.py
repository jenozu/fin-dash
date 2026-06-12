import streamlit as st
from database.database import get_session
from database.models import Account

st.header("Accounts")

session = get_session()
try:
    accounts = session.query(Account).all()
    if accounts:
        for account in accounts:
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 2])
                with c1:
                    st.subheader(account.account_name)
                    st.caption(f"{account.institution_name} — {account.account_type.title()}")
                with c2:
                    st.metric("Current Balance", f"${account.current_balance:,.2f}")
                with c3:
                    st.metric("Available Balance", f"${account.available_balance:,.2f}")
                if account.last_synced:
                    st.caption(f"Last synced: {account.last_synced.strftime('%b %d, %Y %I:%M %p')}")
    else:
        st.info("No accounts connected. Connect your account in Settings.")
finally:
    session.close()
