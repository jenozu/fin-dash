import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import date, timedelta
from services.bill_service import get_all_bills
from services.allocation_service import get_current_balance, calculate_paycheck_allocation
from services.settings_service import get_next_paycheck_date, get_pay_frequency
from config.constants import FREQUENCY_DAYS, PAY_PERIODS_PER_YEAR

st.header("Forecast")
st.caption("Projected cash position over the next 90 days based on paychecks and bills.")

today = date.today()
end_date = today + timedelta(days=90)

balance = get_current_balance()
pay_freq = get_pay_frequency()
next_paycheck = get_next_paycheck_date()
allocation = calculate_paycheck_allocation()

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
    events.append({"date": check_date, "description": "Paycheck", "amount": allocation["paycheck"], "type": "income"})
    check_date += timedelta(days=days_between)

for bill in get_all_bills():
    bill_date = bill.due_date
    freq_days = FREQUENCY_DAYS.get(bill.frequency, 30)
    while bill_date <= end_date:
        if bill_date >= today:
            events.append({"date": bill_date, "description": bill.bill_name, "amount": -bill.amount, "type": "bill"})
        bill_date += timedelta(days=freq_days)

events.sort(key=lambda e: e["date"])

running = balance
timeline = []
for e in events:
    running += e["amount"]
    timeline.append({"Date": e["date"], "Event": e["description"], "Amount": e["amount"], "Balance": running, "Type": e["type"]})

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
        c_a.markdown(f'<span style="color:{color}">{"+ " if amt > 0 else ""}${amt:,.2f}</span>', unsafe_allow_html=True)
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
