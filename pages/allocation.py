import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import date, timedelta
from services.allocation_service import calculate_paycheck_allocation
from services.settings_service import get_pay_frequency, get_next_paycheck_date
from config.constants import PAY_PERIODS_PER_YEAR

st.header("Paycheck Allocation")
st.caption("How each paycheck is distributed across your financial commitments.")

allocation = calculate_paycheck_allocation()
pay_freq = get_pay_frequency()
next_paycheck = get_next_paycheck_date()
paycheck = allocation["paycheck"]

# Top metrics
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Paycheck", f"${paycheck:,.2f}")
c2.metric(
    "Bills",
    f"${allocation['bills']:,.2f}",
    delta=f"{allocation['bills'] / paycheck * 100:.1f}%" if paycheck > 0 else None,
    delta_color="off",
)
c3.metric(
    "Goals",
    f"${allocation['goals']:,.2f}",
    delta=f"{allocation['goals'] / paycheck * 100:.1f}%" if paycheck > 0 else None,
    delta_color="off",
)
c4.metric(
    "Wishlist",
    f"${allocation['wishlist']:,.2f}",
    delta=f"{allocation['wishlist'] / paycheck * 100:.1f}%" if paycheck > 0 else None,
    delta_color="off",
)
avail = allocation["available"]
avail_display = f"${avail:,.2f}" if avail >= 0 else f"-${abs(avail):,.2f}"
c5.metric(
    "Available",
    avail_display,
    delta=f"{avail / paycheck * 100:.1f}%" if paycheck > 0 else None,
    delta_color="off",
)

st.markdown("---")
col_chart, col_formula = st.columns(2)

with col_chart:
    st.subheader("Per-Paycheck Breakdown")
    labels = ["Bills", "Goals", "Wishlist", "Available"]
    values = [
        allocation["bills"],
        allocation["goals"],
        allocation["wishlist"],
        max(allocation["available"], 0),
    ]
    colors = ["#e74c3c", "#3498db", "#f39c12", "#2ecc71"]

    if sum(values) > 0:
        fig = go.Figure()
        for label, value, color in zip(labels, values, colors):
            if value > 0:
                fig.add_trace(go.Bar(
                    name=label,
                    x=[value],
                    y=[""],
                    orientation="h",
                    marker_color=color,
                    text=[f"${value:,.0f}"],
                    textposition="inside",
                    insidetextanchor="middle",
                ))
        fig.update_layout(
            barmode="stack",
            height=120,
            margin=dict(t=10, b=10, l=10, r=10),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="left", x=0),
            xaxis=dict(showticklabels=False, showgrid=False),
            yaxis=dict(showticklabels=False),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

        if allocation["available"] < 0:
            st.warning(
                f"⚠️ Commitments exceed paycheck by "
                f"${abs(allocation['available']):,.2f}. "
                f"Review goals and wishlist targets."
            )
    else:
        st.info("Configure your paycheck amount in Settings.")

with col_formula:
    st.subheader("Formula")

    def _row(label, amount, color, sign="-"):
        cl, cr = st.columns([3, 1])
        cl.write(label)
        cr.markdown(
            f"<div style='text-align:right;color:{color};font-family:monospace'>"
            f"{sign}${amount:,.2f}</div>",
            unsafe_allow_html=True,
        )

    _row("Paycheck Amount", paycheck, "#2ecc71", "+")
    _row("Bills (avg/period)", allocation["bills"], "#e74c3c")
    _row("Goal Contributions", allocation["goals"], "#3498db")
    _row("Wishlist Savings", allocation["wishlist"], "#f39c12")

    st.markdown("<hr style='margin:6px 0'>", unsafe_allow_html=True)

    avail_color = "#2ecc71" if avail >= 0 else "#e74c3c"
    avail_str = f"${avail:,.2f}" if avail >= 0 else f"-${abs(avail):,.2f}"
    cl, cr = st.columns([3, 1])
    cl.markdown("**= Available for Spending**")
    cr.markdown(
        f"<div style='text-align:right;color:{avail_color};font-weight:bold;font-family:monospace'>"
        f"{avail_str}</div>",
        unsafe_allow_html=True,
    )
    st.caption("Bills shown as monthly average ÷ pay periods, not exact per-window amount.")

st.markdown("---")
st.subheader("Next 6 Paychecks")

periods = PAY_PERIODS_PER_YEAR.get(pay_freq, 26)
days_between = int(365 / periods)
paycheck_dates = []
check_date = next_paycheck
for _ in range(6):
    paycheck_dates.append(check_date)
    check_date += timedelta(days=days_between)

rows = []
for pd_date in paycheck_dates:
    avail_val = allocation["available"]
    rows.append({
        "Date": str(pd_date),
        "Paycheck": f"${paycheck:,.2f}",
        "Bills": f"${allocation['bills']:,.2f}",
        "Goals + Wishlist": f"${allocation['goals'] + allocation['wishlist']:,.2f}",
        "Available": f"${avail_val:,.2f}" if avail_val >= 0 else f"-${abs(avail_val):,.2f}",
    })

if rows:
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
