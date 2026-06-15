import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from calendar import monthrange
from datetime import date, timedelta
from services.bill_service import get_all_bills
from services.goal_service import get_all_goals, per_paycheck_for_goal
from services.wishlist_service import get_active_wishlist, per_paycheck_for_item
from services.allocation_service import get_current_balance, calculate_paycheck_allocation
from services.settings_service import get_next_paycheck_date, get_pay_frequency, get_setting
from config.constants import PAY_PERIODS_PER_YEAR

st.header("Forecast")
st.caption("Projected cash position over the next 90 days based on paychecks, bills, and savings commitments.")

today = date.today()
end_date = today + timedelta(days=90)

balance = get_current_balance()
pay_freq = get_pay_frequency()
next_paycheck = get_next_paycheck_date()
allocation = calculate_paycheck_allocation()
min_balance = float(get_setting("min_balance", "0") or "0")

goals = get_all_goals()
wishlist_items = get_active_wishlist()


def _advance_date(current, frequency):
    """Calendar-correct advancement by one billing period."""
    if frequency == "Weekly":
        return current + timedelta(days=7)
    elif frequency == "Bi-Weekly":
        return current + timedelta(days=14)
    elif frequency == "Monthly":
        month = current.month + 1
        year = current.year
        if month > 12:
            month = 1
            year += 1
        return date(year, month, min(current.day, monthrange(year, month)[1]))
    elif frequency == "Quarterly":
        month = current.month + 3
        year = current.year
        if month > 12:
            month -= 12
            year += 1
        return date(year, month, min(current.day, monthrange(year, month)[1]))
    elif frequency == "Annual":
        try:
            return current.replace(year=current.year + 1)
        except ValueError:
            return date(current.year + 1, current.month, 28)
    return current + timedelta(days=30)


c1, c2, c3 = st.columns(3)
c1.metric("Current Balance", f"${balance:,.2f}")
c2.metric("Next Paycheck", str(next_paycheck))
c3.metric("Paycheck Amount", f"${allocation['paycheck']:,.2f}")

st.markdown("---")

# Build event timeline
events = []

periods = PAY_PERIODS_PER_YEAR.get(pay_freq, 26)
days_between = int(365 / periods)
check_date = next_paycheck
while check_date <= end_date:
    events.append({
        "date": check_date,
        "description": "Paycheck",
        "amount": allocation["paycheck"],
        "type": "income",
    })
    for goal in goals:
        per_check = per_paycheck_for_goal(goal, pay_freq)
        if per_check > 0:
            events.append({
                "date": check_date,
                "description": f"Goal: {goal.goal_name}",
                "amount": -per_check,
                "type": "goals",
            })
    for item in wishlist_items:
        per_check = per_paycheck_for_item(item, pay_freq)
        if per_check > 0:
            events.append({
                "date": check_date,
                "description": f"Wishlist: {item.item_name}",
                "amount": -per_check,
                "type": "wishlist",
            })
    check_date += timedelta(days=days_between)

for bill in get_all_bills():
    bill_date = bill.due_date
    while bill_date <= end_date:
        if bill_date >= today:
            events.append({
                "date": bill_date,
                "description": bill.bill_name,
                "amount": -bill.amount,
                "type": "bill",
            })
        bill_date = _advance_date(bill_date, bill.frequency)

events.sort(key=lambda e: e["date"])

running = balance
timeline = []
for e in events:
    running += e["amount"]
    timeline.append({
        "Date": e["date"],
        "Event": e["description"],
        "Amount": e["amount"],
        "Balance": running,
        "Type": e["type"],
    })

if timeline:
    df = pd.DataFrame(timeline)
    chart_df = pd.concat([
        pd.DataFrame([{"Date": today, "Balance": balance}]),
        df[["Date", "Balance"]],
    ]).reset_index(drop=True)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=chart_df["Date"],
        y=chart_df["Balance"],
        mode="lines+markers",
        line=dict(color="#3498db", width=2),
        marker=dict(size=6),
        name="Projected Balance",
        hovertemplate="<b>%{x}</b><br>Balance: $%{y:,.2f}<extra></extra>",
    ))
    fig.add_hline(y=0, line_dash="dash", line_color="red", opacity=0.5, annotation_text="Zero")
    if min_balance > 0:
        fig.add_hline(
            y=min_balance,
            line_dash="dot",
            line_color="orange",
            opacity=0.7,
            annotation_text=f"Min: ${min_balance:,.0f}",
        )
    fig.update_layout(
        title="90-Day Cash Flow Forecast",
        xaxis_title="Date",
        yaxis_title="Balance ($)",
        height=400,
        margin=dict(t=40, b=20),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Upcoming Events")
    for row in timeline[:20]:
        c_d, c_e, c_a, c_b = st.columns([2, 4, 2, 2])
        c_d.write(str(row["Date"]))
        c_e.write(row["Event"])
        amt = row["Amount"]
        color = "green" if amt > 0 else "red"
        sign = "+" if amt > 0 else "-"
        c_a.markdown(
            f'<span style="color:{color}">{sign}${abs(amt):,.2f}</span>',
            unsafe_allow_html=True,
        )
        c_b.write(f"${row['Balance']:,.2f}")
else:
    st.info("No upcoming financial events found. Check that bills and paycheck settings are configured.")

st.markdown("---")
st.subheader("Paycheck Allocation")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Bills", f"${allocation['bills']:,.2f}")
c2.metric("Goals", f"${allocation['goals']:,.2f}")
c3.metric("Wishlist", f"${allocation['wishlist']:,.2f}")
c4.metric("Available Spending", f"${allocation['available']:,.2f}")
