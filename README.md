# fin-dash

A personal finance dashboard built with Streamlit. Tracks accounts, transactions, bills, savings goals, and a wishlist, with Plaid Sandbox sync and a 90-day cash flow forecast.

## Documentation

- [MVP Requirements](docs/MVP.md) — scope and acceptance criteria for Version 1.0
- [Product Requirements Document (PRD)](docs/PRD.md) — full product spec, source of truth

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env  # optional: set PLAID_CLIENT_ID / PLAID_SECRET for Plaid Sandbox sync
streamlit run app.py
```

The SQLite database is created automatically on first run (default path: `database/finance.db`), with schema migrations and sample seed data applied if the database is empty.

## Pages

- **Dashboard** — balance, available cash, spending/income, bills/goals/wishlist overview
- **Accounts** — manage accounts, balance history, role-based categorization
- **Transactions** — filter, add, edit, delete transactions
- **Bills** — recurring bill tracking
- **Goals** — savings goals with per-paycheck contribution targets
- **Wishlist** — planned purchases with savings progress
- **Forecast** — 90-day projected cash flow based on paychecks, bills, and savings commitments
- **Settings** — paycheck configuration and Plaid Sandbox connection

## Tests

```bash
python -m pytest tests/
```

Tests cover the service layer (`services/`) against an isolated SQLite database created per test session, including account/transaction/bill/goal/wishlist CRUD, paycheck allocation math, and Plaid sync (account/transaction upserts, category mapping, error handling).
