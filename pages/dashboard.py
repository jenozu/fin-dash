import streamlit as st
import plotly.express as px
from services.allocation_service import calculate_true_available_cash
from services.transaction_service import get_monthly_spending, get_monthly_income, get_spending_by_category
from services.goal_service import get_all_goals
from services.wishlist_service import get_active_wishlist
from services.bill_service import get_bills_before_paycheck
from services.settings_service import get_next_paycheck_date

st.header("Dashboard")

tac = calculate_true_available_cash()
monthly_spending = get_monthly_spending()
monthly_income = get_monthly_income()
net_cash = monthly_income - monthly_spending
next_paycheck = get_next_paycheck_date()

# Row 1: key metrics
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Current Balance", f"${tac['balance']:,.2f}")
c2.metric(
    "True Available Cash",
    f"${tac['true_available']:,.2f}",
    help="Balance minus bills due before next paycheck, goal contributions, and wishlist savings",
)
c3.metric("Monthly Spending", f"${monthly_spending:,.2f}")
c4.metric("Monthly Income", f"${monthly_income:,.2f}")
c5.metric("Net Cash Flow", f"${net_cash:,.2f}", delta=f"{net_cash:+,.2f}")

st.markdown("---")

# Row 2: balance breakdown + upcoming bills
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Balance Breakdown")
    available = max(tac["true_available"], 0)
    fig = px.pie(
        names=["Available", "Bills", "Goals", "Wishlist"],
        values=[
            available,
            tac["bills_committed"],
            tac["goals_committed"],
            tac["wishlist_committed"],
        ],
        color_discrete_sequence=["#2ecc71", "#e74c3c", "#3498db", "#f39c12"],
        hole=0.45,
    )
    fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=260)
    fig.update_traces(textinfo="percent+label")
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader(f"Bills Before Next Paycheck ({next_paycheck})")
    upcoming = get_bills_before_paycheck()
    if upcoming:
        for bill in upcoming:
            c_a, c_b = st.columns([4, 1])
            c_a.write(f"**{bill.bill_name}** — due {bill.due_date}")
            c_b.write(f"${bill.amount:,.2f}")
        st.markdown(f"**Total committed: ${tac['bills_committed']:,.2f}**")
    else:
        st.info("No bills due before next paycheck.")

st.markdown("---")

# Row 3: spending by category + progress
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

with col_progress:
    st.subheader("Savings Goals")
    for goal in get_all_goals():
        pct = min(goal.current_amount / goal.target_amount, 1.0) if goal.target_amount else 0
        st.write(f"**{goal.goal_name}** — ${goal.current_amount:,.0f} / ${goal.target_amount:,.0f}")
        st.progress(pct)

    st.markdown("---")

    st.subheader("Wishlist")
    for item in get_active_wishlist()[:3]:
        pct = min(item.current_saved / item.estimated_cost, 1.0) if item.estimated_cost else 0
        st.write(f"**{item.item_name}** — ${item.current_saved:,.0f} / ${item.estimated_cost:,.0f}")
        st.progress(pct)
