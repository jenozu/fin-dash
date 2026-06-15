import streamlit as st
import pandas as pd
from datetime import date
from services.transaction_service import get_transactions_df, add_transaction, delete_transaction
from services.account_service import get_all_accounts
from config.constants import TRANSACTION_CATEGORIES

st.header("Transactions")

accounts = get_all_accounts()
account_options = {f"{a.account_name} ({a.account_role or 'Unassigned'})": a.id for a in accounts}

f1, f2, f3, f4 = st.columns(4)
with f1:
    days = st.selectbox("Date Range", [7, 14, 30, 60, 90], index=2, format_func=lambda x: f"Last {x} days")
with f2:
    search = st.text_input("Search merchant", placeholder="e.g. Amazon")
with f3:
    cat_filter = st.selectbox("Category", ["All"] + TRANSACTION_CATEGORIES)
with f4:
    acct_filter = st.selectbox("Account", ["All"] + list(account_options.keys()))

df = get_transactions_df(days)

if not df.empty:
    if search:
        df = df[df["Merchant"].str.contains(search, case=False, na=False)]
    if cat_filter != "All":
        df = df[df["Category"] == cat_filter]
    if acct_filter != "All":
        df = df[df["Account"] == account_options[acct_filter]]

m1, m2, m3 = st.columns(3)
m1.metric("Spending", f"${abs(df[df['Amount'] < 0]['Amount'].sum()):,.2f}" if not df.empty else "$0.00")
m2.metric("Income", f"${df[df['Amount'] > 0]['Amount'].sum():,.2f}" if not df.empty else "$0.00")
m3.metric("Transactions", len(df))

st.markdown("---")

if not df.empty:
    display = df[["Date", "Merchant", "Category", "Amount", "Notes"]].copy()
    display["Amount"] = display["Amount"].apply(lambda x: f"-${abs(x):,.2f}" if x < 0 else f"+${x:,.2f}")
    display["Date"] = pd.to_datetime(display["Date"]).dt.strftime("%b %d, %Y")

    st.dataframe(display, use_container_width=True, hide_index=True)

    with st.expander("Delete a Transaction"):
        txn_labels = {f"{row['Date']} — {row['Merchant']} ({row['Amount']})": idx for idx, row in display.iterrows()}
        if txn_labels:
            to_del = st.selectbox("Select transaction to delete", list(txn_labels.keys()), key="del_txn")
            if st.button("Delete", type="secondary", key="confirm_del"):
                original_idx = txn_labels[to_del]
                txn_id = df.loc[original_idx, "id"]
                delete_transaction(int(txn_id))
                st.success("Transaction deleted.")
                st.rerun()
else:
    st.info("No transactions found.")

st.markdown("---")
with st.expander("Add Transaction"):
    c1, c2 = st.columns(2)
    merchant = c1.text_input("Merchant", key="add_merchant")
    txn_date = c2.date_input("Date", value=date.today(), key="add_date")
    c3, c4 = st.columns(2)
    category = c3.selectbox("Category", TRANSACTION_CATEGORIES, key="add_cat")
    amount_sign = c4.radio("Type", ["Expense (−)", "Income (+)"], horizontal=True, key="add_sign")
    c5, c6 = st.columns(2)
    amount_val = c5.number_input("Amount ($)", min_value=0.01, step=0.01, key="add_amount")
    acct_label = c6.selectbox("Account", ["None"] + list(account_options.keys()), key="add_acct")
    notes = st.text_input("Notes (optional)", key="add_notes")

    if st.button("Add Transaction"):
        if merchant:
            signed_amount = -amount_val if "Expense" in amount_sign else amount_val
            acct_id = account_options.get(acct_label) if acct_label != "None" else None
            add_transaction(merchant, signed_amount, category, txn_date, acct_id, notes or None)
            st.success("Transaction added.")
            st.rerun()
        else:
            st.error("Merchant is required.")
