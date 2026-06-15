import streamlit as st

st.set_page_config(page_title="Money Command Center", layout="wide", initial_sidebar_state="expanded")

if "db_initialized" not in st.session_state:
    from database.schema import init_db, migrate_db
    from mock.seed_data import seed_if_empty
    init_db()
    migrate_db()
    seed_if_empty()
    st.session_state["db_initialized"] = True

with st.sidebar:
    st.title("Money Command Center")
    st.markdown("---")

pg = st.navigation([
    st.Page("pages/dashboard.py", title="Dashboard", default=True),
    st.Page("pages/accounts.py", title="Accounts"),
    st.Page("pages/transactions.py", title="Transactions"),
    st.Page("pages/bills.py", title="Bills"),
    st.Page("pages/goals.py", title="Goals"),
    st.Page("pages/wishlist.py", title="Wishlist"),
    st.Page("pages/budgets.py", title="Budgets"),
    st.Page("pages/allocation.py", title="Allocation"),
    st.Page("pages/forecast.py", title="Forecast"),
    st.Page("pages/settings.py", title="Settings"),
])
pg.run()
