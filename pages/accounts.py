import streamlit as st
import pandas as pd
import plotly.express as px
from services.account_service import (
    get_all_accounts, add_account, update_account_details,
    update_balance, deactivate_account, get_balance_history,
)
from config.constants import ACCOUNT_ROLES, ACCOUNT_TYPES

st.header("Accounts")

accounts = get_all_accounts()

ROLE_COLORS = {
    "Spending": "🟢",
    "Bills Reserve": "🔴",
    "Savings": "🔵",
    "Investment": "🟡",
    "Other": "⚪",
}

if accounts:
    total = sum(a.current_balance for a in accounts)
    spending_bal = next((a.current_balance for a in accounts if a.account_role == "Spending"), 0.0)
    savings_bal = sum(a.current_balance for a in accounts if a.account_role in ("Savings", "Investment"))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Balance", f"${total:,.2f}")
    c2.metric("Spending", f"${spending_bal:,.2f}")
    c3.metric("Savings / Investment", f"${savings_bal:,.2f}")
    c4.metric("Accounts", len(accounts))

    st.markdown("---")

    for acct in accounts:
        badge = ROLE_COLORS.get(acct.account_role or "Other", "⚪")
        role_label = acct.account_role or "Unassigned"
        inst = acct.institution_name or "Unknown"

        with st.container(border=True):
            h1, h2, h3, h4 = st.columns([3, 2, 2, 1])
            with h1:
                st.subheader(f"{badge} {acct.account_name}")
                st.caption(f"{inst} — {acct.account_type.title()} — {role_label}")
            h2.metric("Current Balance", f"${acct.current_balance:,.2f}")
            h3.metric("Available Balance", f"${acct.available_balance:,.2f}")
            with h4:
                expand = st.toggle("Edit", key=f"expand_{acct.id}")

            if expand:
                st.markdown("---")
                tab_bal, tab_edit, tab_hist = st.tabs(["Update Balance", "Edit Details", "History"])

                with tab_bal:
                    new_bal = st.number_input(
                        "New Balance ($)",
                        value=float(acct.current_balance),
                        step=0.01,
                        key=f"bal_{acct.id}",
                    )
                    if st.button("Save Balance", key=f"save_bal_{acct.id}"):
                        update_balance(acct.id, new_bal)
                        st.success("Balance updated and snapshot recorded.")
                        st.rerun()

                with tab_edit:
                    new_name = st.text_input("Account Name", value=acct.account_name, key=f"name_{acct.id}")
                    new_role = st.selectbox(
                        "Role",
                        ACCOUNT_ROLES,
                        index=ACCOUNT_ROLES.index(acct.account_role) if acct.account_role in ACCOUNT_ROLES else 0,
                        key=f"role_{acct.id}",
                    )
                    new_inst = st.text_input("Institution", value=inst if inst != "Unknown" else "", key=f"inst_{acct.id}")
                    col_save, col_del = st.columns([2, 1])
                    with col_save:
                        if st.button("Save Details", key=f"save_det_{acct.id}"):
                            update_account_details(acct.id, new_name, new_role, new_inst)
                            st.success("Details saved.")
                            st.rerun()
                    with col_del:
                        if st.button("Deactivate", key=f"deact_{acct.id}", type="secondary"):
                            deactivate_account(acct.id)
                            st.warning("Account deactivated.")
                            st.rerun()

                with tab_hist:
                    history = get_balance_history(acct.id)
                    if len(history) > 1:
                        hist_df = pd.DataFrame(history)
                        fig = px.line(
                            hist_df, x="date", y="balance",
                            labels={"date": "Date", "balance": "Balance ($)"},
                            markers=True,
                        )
                        fig.update_layout(margin=dict(t=10, b=10), height=220)
                        st.plotly_chart(fig, use_container_width=True)
                    elif len(history) == 1:
                        st.info(f"Opening balance: ${history[0]['balance']:,.2f} on {history[0]['date']}")
                    else:
                        st.info("No balance history yet.")
else:
    st.info("No accounts found. Add one below.")

st.markdown("---")
with st.expander("Add New Account"):
    c1, c2 = st.columns(2)
    new_name = c1.text_input("Account Name", key="new_acct_name")
    new_inst = c2.text_input("Institution", key="new_acct_inst")
    c3, c4, c5 = st.columns(3)
    new_type = c3.selectbox("Type", ACCOUNT_TYPES, key="new_acct_type")
    new_role = c4.selectbox("Role", ACCOUNT_ROLES, key="new_acct_role")
    new_bal = c5.number_input("Opening Balance ($)", min_value=0.0, step=0.01, key="new_acct_bal")

    if st.button("Add Account"):
        if new_name:
            add_account(new_name, new_type, new_role, new_inst, new_bal)
            st.success(f"Added {new_name}.")
            st.rerun()
        else:
            st.error("Account name is required.")
