import streamlit as st
import pandas as pd
from datetime import date
from services.transaction_service import (
    get_transactions_df, add_transaction, update_transaction, delete_transaction,
)
from services.account_service import get_all_accounts
from config.constants import TRANSACTION_CATEGORIES

st.header("Transactions")

accounts = get_all_accounts()
account_map = {a.id: a.account_name for a in accounts}
account_options = {a.account_name: a.id for a in accounts}

# Filters
with st.container(border=True):
    f1, f2, f3, f4 = st.columns(4)
    days_back = f1.selectbox("Date Range", [7, 14, 30, 60, 90], index=2,
                             format_func=lambda d: f"Last {d} days")
    search_merchant = f2.text_input("Search Merchant", placeholder="Filter by merchant...")
    cat_filter = f3.selectbox("Category", ["All"] + TRANSACTION_CATEGORIES)
    acct_names = ["All"] + [a.account_name for a in accounts]
    acct_filter = f4.selectbox("Account", acct_names)

# Add Transaction
with st.expander("+ Add Transaction"):
    with st.form("add_txn_form"):
        t1, t2 = st.columns(2)
        new_merchant = t1.text_input("Merchant / Description")
        new_amount = t2.number_input(
            "Amount ($, negative = expense)", value=-10.00, step=0.01,
        )
        t3, t4 = st.columns(2)
        new_cat = t3.selectbox("Category", TRANSACTION_CATEGORIES)
        new_date = t4.date_input("Date", value=date.today())
        t5, t6 = st.columns(2)
        acct_name_list = list(account_options.keys())
        new_acct_name = t5.selectbox("Account", acct_name_list) if acct_name_list else None
        new_notes = t6.text_input("Notes (optional)")

        if st.form_submit_button("Add Transaction"):
            if not new_merchant.strip():
                st.warning("Merchant/description is required.")
            else:
                acct_id = account_options.get(new_acct_name) if new_acct_name else None
                add_transaction(
                    merchant=new_merchant.strip(),
                    amount=new_amount,
                    category=new_cat,
                    transaction_date=new_date,
                    account_id=acct_id,
                    notes=new_notes,
                )
                st.success("Transaction added.")
                st.rerun()

st.markdown("---")

# Load transactions
selected_acct_id = account_options.get(acct_filter) if acct_filter != "All" else None
df = get_transactions_df(days=days_back, account_id=selected_acct_id)

# Apply text/category filters
if not df.empty:
    if search_merchant:
        df = df[df["Merchant"].str.contains(search_merchant, case=False, na=False)]
    if cat_filter != "All":
        df = df[df["Category"] == cat_filter]

if df.empty:
    st.info("No transactions match the current filters.")
else:
    # Replace account_id with name for display
    df = df.copy()
    df["Account"] = df["Account"].map(account_map).fillna("Unknown")

    # Store original for diff
    original_df = df.copy()

    st.markdown(f"**{len(df)} transaction(s)**")

    edited_df = st.data_editor(
        df,
        key="txn_editor",
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
            "Date": st.column_config.DateColumn("Date"),
            "Merchant": st.column_config.TextColumn("Merchant"),
            "Category": st.column_config.SelectboxColumn(
                "Category", options=TRANSACTION_CATEGORIES
            ),
            "Amount": st.column_config.NumberColumn("Amount ($)", format="%.2f"),
            "Account": st.column_config.TextColumn("Account", disabled=True),
            "Notes": st.column_config.TextColumn("Notes"),
            "Manual": st.column_config.CheckboxColumn("Manual", disabled=True),
        },
        hide_index=True,
    )

    if st.button("Save Changes", type="primary"):
        changes = 0
        errors = 0

        orig_ids = set(original_df["id"].dropna().astype(int).tolist())
        edited_ids = (
            set(edited_df["id"].dropna().astype(int).tolist())
            if "id" in edited_df.columns else set()
        )

        # Deletions
        for tid in orig_ids - edited_ids:
            if delete_transaction(int(tid)):
                changes += 1
            else:
                errors += 1

        for _, row in edited_df.iterrows():
            row_id = row.get("id")

            # New rows (no id)
            if pd.isna(row_id) if row_id is not None else True:
                merchant = str(row.get("Merchant", "")).strip()
                if not merchant:
                    continue
                acct_name = row.get("Account", "")
                acct_id = account_options.get(acct_name)
                try:
                    add_transaction(
                        merchant=merchant,
                        amount=float(row.get("Amount", 0)),
                        category=str(row.get("Category", "")),
                        transaction_date=row.get("Date") or date.today(),
                        account_id=acct_id,
                        notes=str(row.get("Notes", "")),
                    )
                    changes += 1
                except Exception:
                    errors += 1
                continue

            # Updates — compare against original
            tid = int(row_id)
            orig_rows = original_df[original_df["id"] == tid]
            if orig_rows.empty:
                continue
            orig_row = orig_rows.iloc[0]

            changed = (
                str(row.get("Merchant", "")) != str(orig_row.get("Merchant", ""))
                or float(row.get("Amount", 0)) != float(orig_row.get("Amount", 0))
                or str(row.get("Category", "")) != str(orig_row.get("Category", ""))
                or str(row.get("Notes", "")) != str(orig_row.get("Notes", ""))
                or row.get("Date") != orig_row.get("Date")
            )
            if changed:
                try:
                    update_transaction(
                        txn_id=tid,
                        merchant=str(row.get("Merchant", "")).strip(),
                        amount=float(row.get("Amount", 0)),
                        category=str(row.get("Category", "")),
                        transaction_date=row.get("Date") or date.today(),
                        notes=str(row.get("Notes", "")),
                    )
                    changes += 1
                except Exception:
                    errors += 1

        if errors:
            st.error(f"{errors} error(s) saving changes.")
        if changes:
            st.success(f"Saved {changes} change(s).")
            st.rerun()
        else:
            st.info("No changes detected.")

    # Summary totals
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    income = df[df["Amount"] > 0]["Amount"].sum()
    expenses = df[df["Amount"] < 0]["Amount"].sum()
    net = income + expenses
    col1.metric("Income", f"${income:,.2f}")
    col2.metric("Expenses", f"-${abs(expenses):,.2f}")
    sign = "-" if net < 0 else ""
    col3.metric("Net", f"{sign}${abs(net):,.2f}")
