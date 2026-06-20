import streamlit as st
from datetime import datetime
from config.constants import PAY_FREQUENCIES
from services.settings_service import get_setting, set_setting, get_pay_frequency, get_average_paycheck, get_next_paycheck_date
from services.plaid_service import is_configured

st.header("Settings")

# ── Paycheck Settings ──────────────────────────────────────────────
st.subheader("Paycheck Settings")
with st.form("paycheck_settings_form"):
    pay_freq = get_pay_frequency()
    freq_idx = PAY_FREQUENCIES.index(pay_freq) if pay_freq in PAY_FREQUENCIES else 1
    avg_check = get_average_paycheck()
    next_paycheck = get_next_paycheck_date()

    c1, c2 = st.columns(2)
    new_freq = c1.selectbox("Pay Frequency", PAY_FREQUENCIES, index=freq_idx)
    new_check = c2.number_input("Average Paycheck ($)", min_value=0.0, value=avg_check, step=50.0)
    new_date = st.date_input("Next Paycheck Date", value=next_paycheck)

    if st.form_submit_button("Save Settings"):
        set_setting("pay_frequency", new_freq)
        set_setting("average_paycheck", new_check)
        set_setting("next_paycheck_date", str(new_date))
        st.success("Settings saved.")
        st.rerun()

st.markdown("---")

# ── Plaid Integration ──────────────────────────────────────────────
st.subheader("Plaid Integration")

plaid_configured = is_configured()
access_token = get_setting("plaid_access_token", "")
plaid_item_id = get_setting("plaid_item_id", "")
last_sync = get_setting("plaid_last_sync", "")

if not plaid_configured:
    st.warning(
        "Plaid credentials not configured. "
        "Add `PLAID_CLIENT_ID` and `PLAID_SECRET` to your `.env` file, then restart the app."
    )
    with st.expander("How to set up Plaid Sandbox"):
        st.markdown("""
1. Create a free account at [dashboard.plaid.com](https://dashboard.plaid.com)
2. Go to **Team Settings → Keys** and copy your **Sandbox** `client_id` and `secret`
3. Create a `.env` file in the project root:
```
PLAID_CLIENT_ID=your_client_id_here
PLAID_SECRET=your_sandbox_secret_here
PLAID_ENV=sandbox
```
4. Restart the app — the Connect button will appear here
""")

elif not access_token:
    # Configured but not connected
    st.info("Credentials loaded. Connect First Platypus Bank (Plaid Sandbox) to sync real account data.")

    col_connect, col_manual = st.columns(2)
    with col_connect:
        if st.button("Connect First Platypus Bank (Sandbox)", type="primary"):
            with st.spinner("Connecting to Plaid Sandbox..."):
                try:
                    from services.plaid_service import create_sandbox_token, exchange_public_token
                    pub_token = create_sandbox_token()
                    result = exchange_public_token(pub_token)
                    set_setting("plaid_access_token", result["access_token"])
                    set_setting("plaid_item_id", result["item_id"])
                    st.success("Connected! Click 'Sync Now' to pull accounts and transactions.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Connection failed: {e}")

    with col_manual:
        st.caption("Or enter a public_token manually (from Plaid Link):")
        manual_token = st.text_input("Public Token", placeholder="public-sandbox-...")
        if st.button("Exchange Token") and manual_token:
            try:
                from services.plaid_service import exchange_public_token
                result = exchange_public_token(manual_token)
                set_setting("plaid_access_token", result["access_token"])
                set_setting("plaid_item_id", result["item_id"])
                st.success("Token exchanged successfully.")
                st.rerun()
            except Exception as e:
                st.error(f"Exchange failed: {e}")

else:
    # Connected
    st.success(f"Plaid connected. Item ID: `{plaid_item_id}`")
    if last_sync:
        st.caption(f"Last synced: {last_sync}")
    else:
        st.caption("Not yet synced — click Sync Now to pull data.")

    col_sync, col_disconnect = st.columns([2, 1])

    with col_sync:
        if st.button("Sync Now", type="primary"):
            with st.spinner("Syncing accounts and transactions..."):
                try:
                    from services.plaid_service import get_accounts, sync_transactions
                    from services.account_service import upsert_plaid_accounts
                    from services.transaction_service import upsert_plaid_transactions

                    # Sync accounts
                    plaid_accts = get_accounts(access_token)
                    acct_result = upsert_plaid_accounts(plaid_accts, plaid_item_id)

                    # Sync transactions (incremental using cursor)
                    cursor = get_setting("plaid_cursor", "") or None
                    txn_data = sync_transactions(access_token, cursor)
                    txn_result = upsert_plaid_transactions(
                        txn_data["added"], txn_data["modified"], txn_data["removed"]
                    )

                    # Save cursor for next incremental sync
                    if txn_data["next_cursor"]:
                        set_setting("plaid_cursor", txn_data["next_cursor"])
                    set_setting("plaid_last_sync", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

                    st.success(
                        f"Sync complete — "
                        f"Accounts: {acct_result['created']} new, {acct_result['updated']} updated | "
                        f"Transactions: {txn_result['inserted']} new, "
                        f"{txn_result['updated']} updated, {txn_result['deleted']} removed"
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"Sync failed: {e}")

    with col_disconnect:
        if st.button("Disconnect", type="secondary"):
            set_setting("plaid_access_token", "")
            set_setting("plaid_item_id", "")
            set_setting("plaid_cursor", "")
            set_setting("plaid_last_sync", "")
            st.info("Plaid disconnected. Manual data is preserved.")
            st.rerun()

    with st.expander("Sync notes"):
        st.markdown("""
- **Accounts**: balanced updated each sync; role preserved if you set it manually
- **Transactions**: new/changed pulled incrementally via cursor; removed flagged by Plaid are deleted
- **Manual data is never overwritten**: accounts and transactions without a Plaid ID are untouched
- Re-syncing is safe — duplicate protection via `plaid_transaction_id`
""")
