import streamlit as st
from config.constants import PAY_FREQUENCIES
from services.settings_service import get_setting, set_setting, get_pay_frequency, get_average_paycheck, get_next_paycheck_date

st.header("Settings")

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

    if st.form_submit_button("Save Paycheck Settings"):
        set_setting("pay_frequency", new_freq)
        set_setting("average_paycheck", new_check)
        set_setting("next_paycheck_date", str(new_date))
        st.success("Paycheck settings saved.")
        st.rerun()

st.markdown("---")
st.subheader("Bills Reserve Account")
st.caption("Optional: name of the account you keep bill money in (for reference only).")
with st.form("reserve_account_form"):
    current_reserve = get_setting("reserve_account_name", "")
    new_reserve = st.text_input(
        "Reserve Account Name",
        value=current_reserve,
        placeholder="e.g. Bills Checking",
    )
    if st.form_submit_button("Save Reserve Account"):
        set_setting("reserve_account_name", new_reserve)
        st.success("Reserve account name saved.")
        st.rerun()

st.markdown("---")
st.subheader("Plaid Integration")
st.info(
    "Plaid account connection will be available in a future update. "
    "The app is currently running on mock data."
)

plaid_status = get_setting("plaid_access_token", "")
if plaid_status:
    st.success("Plaid account connected.")
    if st.button("Disconnect Account"):
        set_setting("plaid_access_token", "")
        set_setting("plaid_item_id", "")
        st.success("Account disconnected.")
        st.rerun()
else:
    st.warning("No Plaid account connected. Using mock data.")
