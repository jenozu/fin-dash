import streamlit as st
from config.constants import TRANSACTION_CATEGORIES
from services.budget_service import (
    get_all_budgets, get_budget_vs_actual, add_budget, update_budget, delete_budget,
)

st.header("Budgets")

df = get_budget_vs_actual(days=30)
budgets = get_all_budgets()
budgeted_cats = {b.category for b in budgets}

# Summary metrics
if not df.empty:
    total_limit = df["monthly_limit"].sum()
    total_actual = df["actual"].sum()
    over_count = int((df["actual"] > df["monthly_limit"]).sum())

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Budgeted", f"${total_limit:,.2f}")
    c2.metric("Total Spent (30d)", f"${total_actual:,.2f}")
    c3.metric("Over Budget", str(over_count), delta=f"{over_count} categories" if over_count else None,
              delta_color="inverse")

st.markdown("---")

# Budget list with inline edit
if df.empty and not budgets:
    st.info("No budgets set. Add one below.")
else:
    for _, row in df.iterrows():
        cat = row["category"]
        limit = row["monthly_limit"]
        actual = row["actual"]
        pct = min(row["pct_used"], 1.0)
        remaining = row["remaining"]

        if pct >= 1.0:
            bar_color = "#e74c3c"
            status_icon = "🔴"
        elif pct >= 0.8:
            bar_color = "#f39c12"
            status_icon = "🟡"
        else:
            bar_color = "#2ecc71"
            status_icon = "🟢"

        edit_key = f"edit_budget_{cat}"

        with st.container(border=True):
            col_a, col_b, col_c, col_d = st.columns([3, 2, 2, 1])
            col_a.markdown(f"{status_icon} **{cat}**")
            col_b.markdown(f"Spent: **${actual:,.2f}** / ${limit:,.2f}")
            if remaining >= 0:
                col_c.markdown(f"Remaining: **${remaining:,.2f}**")
            else:
                col_c.markdown(
                    f"<span style='color:#e74c3c'>Over by **${abs(remaining):,.2f}**</span>",
                    unsafe_allow_html=True,
                )
            btn_col, del_col = col_d.columns(2)
            if btn_col.button("Edit", key=f"editbtn_{cat}"):
                st.session_state[edit_key] = True
            if del_col.button("✕", key=f"delbtn_{cat}", help="Remove budget"):
                st.session_state[f"confirm_del_{cat}"] = True

            st.progress(pct)

            if st.session_state.get(f"confirm_del_{cat}"):
                st.warning(f"Remove budget for **{cat}**?")
                cc1, cc2 = st.columns(2)
                budget_obj = next((b for b in budgets if b.category == cat), None)
                if cc1.button("Yes, Remove", key=f"del_yes_{cat}"):
                    if budget_obj:
                        delete_budget(budget_obj.id)
                    st.session_state.pop(f"confirm_del_{cat}", None)
                    st.rerun()
                if cc2.button("Cancel", key=f"del_no_{cat}"):
                    st.session_state.pop(f"confirm_del_{cat}", None)
                    st.rerun()

            if st.session_state.get(edit_key):
                budget_obj = next((b for b in budgets if b.category == cat), None)
                with st.form(f"edit_form_{cat}"):
                    new_limit = st.number_input(
                        "Monthly Limit ($)",
                        value=float(limit),
                        min_value=0.01,
                        step=10.0,
                    )
                    s1, s2 = st.columns(2)
                    if s1.form_submit_button("Save"):
                        if budget_obj:
                            update_budget(budget_obj.id, new_limit)
                        st.session_state.pop(edit_key, None)
                        st.rerun()
                    if s2.form_submit_button("Cancel"):
                        st.session_state.pop(edit_key, None)
                        st.rerun()

st.markdown("---")
st.subheader("Add Budget")

available_cats = [c for c in TRANSACTION_CATEGORIES if c not in budgeted_cats and c != "Income"]

if not available_cats:
    st.info("All categories already have a budget. Edit or remove existing ones above.")
else:
    with st.form("add_budget_form"):
        a1, a2 = st.columns(2)
        new_cat = a1.selectbox("Category", available_cats)
        new_limit = a2.number_input("Monthly Limit ($)", value=100.0, min_value=0.01, step=10.0)

        if st.form_submit_button("Add Budget"):
            add_budget(new_cat, new_limit)
            st.success(f"Budget set: {new_cat} — ${new_limit:,.2f}/month")
            st.rerun()
