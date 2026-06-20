import streamlit as st
import pandas as pd
from datetime import date
from services.transaction_service import get_transactions_df, add_transaction, update_transaction, delete_transaction
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
    display = df[["Date", "Merchant", "Category", "Amount", "Notes", "Pending"]].copy()
    display["Amount"] = display["Amount"].apply(lambda x: f"-${abs(x):,.2f}" if x < 0 else f"+${x:,.2f}")
    display["Date"] = pd.to_datetime(display["Date"]).dt.strftime("%b %d, %Y")
    display["Status"] = display["Pending"].apply(lambda p: "⏳ Pending" if p else "✅ Posted")
    display = display.drop(columns=["Pending"])

    st.dataframe(display, use_container_width=True, hide_index=True)

    with st.expander("Edit a Transaction"):
        txn_labels = {f"{row['Date']} — {row['Merchant']} ({row['Amount']})": idx for idx, row in display.iterrows()}
        if txn_labels:
            to_edit = st.selectbox("Select transaction to edit", list(txn_labels.keys()), key="edit_txn")
            original_idx = txn_labels[to_edit]
            txn_row = df.loc[original_idx]
            with st.form("edit_txn_form"):
                e1, e2 = st.columns(2)
                edit_merchant = e1.text_input("Merchant", value=txn_row["Merchant"], key="edit_merchant")
                edit_date = e2.date_input("Date", value=pd.to_datetime(txn_row["Date"]).date(), key="edit_date")
                e3, e4 = st.columns(2)
                edit_category = e3.selectbox(
                    "Category", TRANSACTION_CATEGORIES,
                    index=TRANSACTION_CATEGORIES.index(txn_row["Category"]) if txn_row["Category"] in TRANSACTION_CATEGORIES else 0,
                    key="edit_cat",
                )
                edit_sign = e4.radio("Type", ["Expense (−)", "Income (+)"], index=0 if txn_row["Amount"] < 0 else 1, horizontal=True, key="edit_sign")
                e5, e6 = st.columns(2)
                edit_amount_val = e5.number_input("Amount ($)", min_value=0.01, step=0.01, value=abs(float(txn_row["Amount"])), key="edit_amount")
                edit_notes = e6.text_input("Notes (optional)", value=txn_row["Notes"], key="edit_notes")
                if st.form_submit_button("Save Changes"):
                    signed_amount = -edit_amount_val if "Expense" in edit_sign else edit_amount_val
                    update_transaction(int(txn_row["id"]), edit_merchant, signed_amount, edit_category, edit_date, edit_notes or None)
                    st.success("Transaction updated.")
                    st.rerun()

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
