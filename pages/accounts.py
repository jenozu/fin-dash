import streamlit as st
import plotly.graph_objects as go
from services.account_service import (
    get_all_accounts, add_account, update_account_details,
    update_balance, deactivate_account, get_balance_history,
)
from config.constants import ACCOUNT_ROLES, ACCOUNT_TYPES, ACCOUNT_SUBTYPES

st.header("Accounts")

ROLE_COLORS = {
    "Spending": "#2ecc71",
    "Bills Reserve": "#e74c3c",
    "Savings": "#3498db",
    "General": "#95a5a6",
}

accounts = get_all_accounts()

# Summary metrics
depository_total = sum(
    a.current_balance for a in accounts if a.account_type == "depository"
)
spending_acct = next((a for a in accounts if a.account_role == "Spending"), None)
bills_acct = next((a for a in accounts if a.account_role == "Bills Reserve"), None)
savings_acct = next((a for a in accounts if a.account_role == "Savings"), None)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Assets", f"${depository_total:,.2f}")
col2.metric("Spending", f"${spending_acct.current_balance:,.2f}" if spending_acct else "—")
col3.metric("Bills Reserve", f"${bills_acct.current_balance:,.2f}" if bills_acct else "—")
col4.metric("Savings", f"${savings_acct.current_balance:,.2f}" if savings_acct else "—")

st.markdown("---")

if not accounts:
    st.info("No accounts yet. Add one below.")
else:
    for account in accounts:
        role = account.account_role or "General"
        role_color = ROLE_COLORS.get(role, "#95a5a6")
        last_synced = account.last_synced.strftime("%b %d, %Y %H:%M") if account.last_synced else "—"

        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 3])
            with col1:
                st.markdown(
                    f"**{account.account_name}** "
                    f"<span style='background:{role_color};color:white;"
                    f"padding:2px 8px;border-radius:4px;font-size:0.75em'>{role}</span>",
                    unsafe_allow_html=True,
                )
                parts = []
                if account.institution_name:
                    parts.append(account.institution_name)
                if account.account_type:
                    parts.append(account.account_type)
                if account.account_subtype:
                    parts.append(account.account_subtype)
                st.caption(" · ".join(parts))
                st.caption(f"Updated: {last_synced}")

            col2.metric("Current Balance", f"${account.current_balance:,.2f}")
            col3.metric("Available Balance", f"${account.available_balance:,.2f}")

            with col4:
                btn1, btn2, btn3 = st.columns(3)
                bal_key = f"bal_{account.id}"
                edit_key = f"edit_acct_{account.id}"

                if btn1.button("Update", key=f"balbtn_{account.id}"):
                    st.session_state[bal_key] = True
                if btn2.button("Edit", key=f"editbtn_{account.id}"):
                    st.session_state[edit_key] = True
                if btn3.button("✕", key=f"delbtn_{account.id}", help="Deactivate account"):
                    st.session_state[f"confirm_del_{account.id}"] = True

            # Deactivate confirmation
            if st.session_state.get(f"confirm_del_{account.id}"):
                st.warning(
                    f"Deactivate **{account.account_name}**? "
                    f"This hides it but preserves history."
                )
                c1, c2 = st.columns(2)
                if c1.button("Yes, Deactivate", key=f"confirm_yes_{account.id}"):
                    deactivate_account(account.id)
                    st.session_state.pop(f"confirm_del_{account.id}", None)
                    st.rerun()
                if c2.button("Cancel", key=f"confirm_no_{account.id}"):
                    st.session_state.pop(f"confirm_del_{account.id}", None)
                    st.rerun()

            # Update Balance form
            if st.session_state.get(bal_key):
                with st.form(f"bal_form_{account.id}"):
                    b1, b2 = st.columns(2)
                    new_current = b1.number_input(
                        "Current Balance ($)",
                        value=account.current_balance,
                        step=0.01,
                    )
                    new_available = b2.number_input(
                        "Available Balance ($)",
                        value=account.available_balance,
                        step=0.01,
                    )
                    bal_notes = st.text_input("Notes (optional)")
                    s1, s2 = st.columns(2)
                    if s1.form_submit_button("Save Balance"):
                        update_balance(account.id, new_current, new_available, bal_notes)
                        st.session_state.pop(bal_key, None)
                        st.success("Balance updated and snapshot recorded.")
                        st.rerun()
                    if s2.form_submit_button("Cancel"):
                        st.session_state.pop(bal_key, None)
                        st.rerun()

            # Edit Account Details form
            if st.session_state.get(edit_key):
                with st.form(f"edit_acct_form_{account.id}"):
                    e1, e2 = st.columns(2)
                    edit_name = e1.text_input("Account Name", value=account.account_name)
                    edit_institution = e2.text_input(
                        "Institution", value=account.institution_name or ""
                    )
                    e3, e4, e5 = st.columns(3)
                    edit_type = e3.selectbox(
                        "Type", ACCOUNT_TYPES,
                        index=ACCOUNT_TYPES.index(account.account_type)
                        if account.account_type in ACCOUNT_TYPES else 0,
                    )
                    subtype_options = ["(none)"] + ACCOUNT_SUBTYPES
                    current_subtype = account.account_subtype or "(none)"
                    edit_subtype = e4.selectbox(
                        "Subtype", subtype_options,
                        index=subtype_options.index(current_subtype)
                        if current_subtype in subtype_options else 0,
                    )
                    role_options = ["(none)"] + ACCOUNT_ROLES
                    current_role = account.account_role or "(none)"
                    edit_role = e5.selectbox(
                        "Role", role_options,
                        index=role_options.index(current_role)
                        if current_role in role_options else 0,
                    )
                    s1, s2 = st.columns(2)
                    if s1.form_submit_button("Save"):
                        if not edit_name.strip():
                            st.warning("Account name is required.")
                        else:
                            update_account_details(
                                account.id,
                                edit_name.strip(),
                                edit_type,
                                edit_subtype if edit_subtype != "(none)" else None,
                                edit_role if edit_role != "(none)" else None,
                                edit_institution,
                            )
                            st.session_state.pop(edit_key, None)
                            st.rerun()
                    if s2.form_submit_button("Cancel"):
                        st.session_state.pop(edit_key, None)
                        st.rerun()

            # Balance History
            history = get_balance_history(account.id, limit=30)
            if history:
                with st.expander(f"Balance History ({len(history)} snapshots)"):
                    if len(history) >= 2:
                        dates = [s.snapshot_date for s in history]
                        balances = [s.balance for s in history]
                        fig = go.Figure(go.Scatter(
                            x=dates,
                            y=balances,
                            mode="lines+markers",
                            line=dict(color=role_color, width=2),
                        ))
                        fig.update_layout(
                            height=200,
                            margin=dict(t=10, b=10, l=10, r=10),
                            yaxis_title="Balance ($)",
                            xaxis_title=None,
                        )
                        st.plotly_chart(fig, use_container_width=True)

                    for snap in reversed(history[-5:]):
                        st.markdown(
                            f"- {snap.snapshot_date.strftime('%b %d, %Y')} — "
                            f"${snap.balance:,.2f}"
                            + (f" · {snap.notes}" if snap.notes else "")
                        )

st.markdown("---")
st.subheader("Add Account")
with st.form("add_account_form"):
    a1, a2 = st.columns(2)
    new_name = a1.text_input("Account Name")
    new_institution = a2.text_input("Institution Name")
    a3, a4, a5 = st.columns(3)
    new_type = a3.selectbox("Type", ACCOUNT_TYPES)
    new_subtype = a4.selectbox("Subtype", ["(none)"] + ACCOUNT_SUBTYPES)
    new_role = a5.selectbox("Role", ["(none)"] + ACCOUNT_ROLES)
    a6, a7 = st.columns(2)
    new_current_bal = a6.number_input("Current Balance ($)", value=0.0, step=0.01)
    new_avail_bal = a7.number_input("Available Balance ($)", value=0.0, step=0.01)

    if st.form_submit_button("Add Account"):
        if not new_name.strip():
            st.warning("Account name is required.")
        else:
            add_account(
                account_name=new_name.strip(),
                account_type=new_type,
                account_subtype=new_subtype if new_subtype != "(none)" else None,
                account_role=new_role if new_role != "(none)" else None,
                institution_name=new_institution,
                current_balance=new_current_bal,
                available_balance=new_avail_bal,
            )
            st.success(f"Added account: {new_name}")
            st.rerun()
