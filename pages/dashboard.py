import streamlit as st
import plotly.express as px
from datetime import date
from services.allocation_service import calculate_true_available_cash
from services.transaction_service import get_monthly_spending, get_monthly_income, get_spending_by_category
from services.goal_service import get_all_goals
from services.wishlist_service import get_active_wishlist
from services.bill_service import get_bills_before_paycheck
from services.settings_service import get_next_paycheck_date, get_setting

st.header("Dashboard")

tac = calculate_true_available_cash()
monthly_spending = get_monthly_spending()
monthly_income = get_monthly_income()
net_cash = monthly_income - monthly_spending
next_paycheck = get_next_paycheck_date()
today = date.today()
tac_alert = float(get_setting("tac_alert_threshold", "0") or "0")

# Row 1: key metrics
tac_val = tac["true_available"]
tac_display = f"${tac_val:,.2f}" if tac_val >= 0 else f"-${abs(tac_val):,.2f}"

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Current Balance", f"${tac['balance']:,.2f}")
c2.metric(
    "True Available Cash",
    tac_display,
    help="Balance minus bills due before next paycheck, goal contributions, and wishlist savings",
)
c3.metric("Monthly Spending", f"${monthly_spending:,.2f}")
c4.metric("Monthly Income", f"${monthly_income:,.2f}")
c5.metric("Net Cash Flow", f"${net_cash:,.2f}", delta=f"{net_cash:+,.2f}")

st.markdown("---")

# Row 2: TAC formula breakdown + upcoming bills
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("True Available Cash")

    def _row(label, amount, color, sign):
        cl, cr = st.columns([3, 1])
        cl.write(label)
        cr.markdown(
            f"<div style='text-align:right;color:{color};font-family:monospace'>"
            f"{sign}${amount:,.2f}</div>",
            unsafe_allow_html=True,
        )

    _row("Current Balance",       tac["balance"],            "#2ecc71", "+")
    _row("Bills Before Paycheck", tac["bills_committed"],    "#e74c3c", "-")
    _row("Goal Contributions",    tac["goals_committed"],    "#3498db", "-")
    _row("Wishlist Savings",      tac["wishlist_committed"], "#f39c12", "-")

    st.markdown("<hr style='margin:6px 0'>", unsafe_allow_html=True)

    tac_color = "#2ecc71" if tac_val >= 0 else "#e74c3c"
    tac_str = f"${tac_val:,.2f}" if tac_val >= 0 else f"-${abs(tac_val):,.2f}"
    cl, cr = st.columns([3, 1])
    cl.markdown("**= True Available Cash**")
    cr.markdown(
        f"<div style='text-align:right;color:{tac_color};font-weight:bold;font-family:monospace'>"
        f"{tac_str}</div>",
        unsafe_allow_html=True,
    )
    st.caption(f"Paycheck window: today through {next_paycheck}")

    if tac_alert > 0 and tac_val < tac_alert:
        st.warning(f"⚠️ True Available Cash ({tac_str}) is below your alert threshold of ${tac_alert:,.2f}.")

with col_right:
    st.subheader(f"Bills Before Next Paycheck ({next_paycheck})")
    upcoming = get_bills_before_paycheck()
    if upcoming:
        for bill in upcoming:
            days = (bill.due_date - today).days
            if days < 0:
                label = f"**{bill.bill_name}** — ⚠️ overdue ({abs(days)}d)"
            else:
                label = f"**{bill.bill_name}** — due {bill.due_date}"
            c_a, c_b = st.columns([4, 1])
            c_a.write(label)
            c_b.write(f"${bill.amount:,.2f}")
        st.markdown(f"**Total committed: ${tac['bills_committed']:,.2f}**")
    else:
        st.info("No bills due before next paycheck.")

st.markdown("---")

# Row 3: spending by category + goals/wishlist progress
col_chart, col_progress = st.columns(2)

with col_chart:
    st.subheader("Spending by Category (30 days)")
    cat_df = get_spending_by_category()
    if not cat_df.empty:
        fig2 = px.bar(
            cat_df,
            x="Amount",
            y="Category",
            orientation="h",
            color="Amount",
            color_continuous_scale="Blues",
            labels={"Amount": "Spent ($)"},
        )
        fig2.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            height=320,
            coloraxis_showscale=False,
            yaxis=dict(categoryorder="total ascending"),
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No spending data for the last 30 days.")

with col_progress:
    goals = get_all_goals()
    if goals:
        st.subheader("Savings Goals")
        for goal in goals:
            pct = min(goal.current_amount / goal.target_amount, 1.0) if goal.target_amount else 0
            st.write(f"**{goal.goal_name}** — ${goal.current_amount:,.0f} / ${goal.target_amount:,.0f}")
            st.progress(pct)

    items = get_active_wishlist()[:3]
    if items:
        st.markdown("---")
        st.subheader("Wishlist")
        for item in items:
            pct = min(item.current_saved / item.estimated_cost, 1.0) if item.estimated_cost else 0
            st.write(f"**{item.item_name}** — ${item.current_saved:,.0f} / ${item.estimated_cost:,.0f}")
            st.progress(pct)
