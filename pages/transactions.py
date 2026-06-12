import streamlit as st
import pandas as pd
from services.transaction_service import get_transactions_df

st.header("Transactions")

c1, c2, c3 = st.columns(3)
with c1:
    days = st.selectbox("Date Range", [7, 14, 30, 60, 90], index=2, format_func=lambda x: f"Last {x} days")
with c2:
    search = st.text_input("Search merchant", placeholder="e.g. Amazon")

df = get_transactions_df(days)

with c3:
    categories = ["All"] + sorted(df["Category"].dropna().unique().tolist()) if not df.empty else ["All"]
    category_filter = st.selectbox("Category", categories)

if not df.empty:
    if search:
        df = df[df["Merchant"].str.contains(search, case=False, na=False)]
    if category_filter != "All":
        df = df[df["Category"] == category_filter]

    col_s, col_i, col_c = st.columns(3)
    col_s.metric("Spending", f"${abs(df[df['Amount'] < 0]['Amount'].sum()):,.2f}")
    col_i.metric("Income", f"${df[df['Amount'] > 0]['Amount'].sum():,.2f}")
    col_c.metric("Transactions", len(df))

    st.markdown("---")

    display = df.copy()
    display["Amount"] = display["Amount"].apply(
        lambda x: f"-${abs(x):,.2f}" if x < 0 else f"+${x:,.2f}"
    )
    display["Date"] = pd.to_datetime(display["Date"]).dt.strftime("%b %d, %Y")
    st.dataframe(display, use_container_width=True, hide_index=True)
else:
    st.info("No transactions found.")
