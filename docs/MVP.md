# Fin-Dash MVP (Version 1.0)

## Purpose

Fin-Dash helps users answer one critical question:

> "How much money can I safely spend today without hurting my future goals?"

Unlike traditional budgeting apps that focus on tracking past spending, Fin-Dash focuses on future commitments, savings goals, planned purchases, and paycheck allocation.

The MVP is complete when a user can:

1. Connect or manually manage their accounts
2. Track transactions
3. Manage recurring bills
4. Create savings goals
5. Create wishlist purchases
6. Forecast future cash flow
7. View True Available Cash (TAC)
8. Plan paycheck allocations
9. Sync data from Plaid

---

# Success Criteria

A user should be able to:

- Open the app
- Connect their bank account (or manually enter balances)
- See their True Available Cash
- See upcoming bills
- See goal funding requirements
- See wishlist funding requirements
- Forecast future balances
- Determine whether they can afford a purchase

without using spreadsheets.

---

# Core MVP Features

---

# 1. Dashboard

## Goal

Provide a single-screen overview of financial health.

## Requirements

### Metrics

- Total Account Balance
- Bills Committed
- Goals Committed
- Wishlist Committed
- True Available Cash (TAC)

### Upcoming Bills

Display:

- Bill Name
- Due Date
- Amount
- Funding Status

### Goals Summary

Display:

- Goal Name
- Current Amount
- Target Amount
- Progress %

### Wishlist Summary

Display:

- Item Name
- Current Saved
- Target Cost
- Progress %

### Forecast Summary

Display:

- Next paycheck date
- Projected balance
- TAC warning status

### Acceptance Criteria

- Dashboard loads in under 3 seconds
- All values update automatically when data changes
- TAC always reflects latest commitments

---

# 2. Accounts

## Goal

Manage all financial accounts.

## Requirements

### Account Types

- Checking
- Savings
- Investment
- Credit Card
- Cash

### Account Roles

- Spending
- Bills Reserve
- Savings
- Investment

### Features

- Create account
- Edit account
- Deactivate account
- View balance
- View balance history
- Manually update balance

### Balance History

Store:

- Date
- Balance

Display:

- Trend chart

### Acceptance Criteria

- Multiple accounts supported
- One account designated as Spending Account
- TAC uses Spending Account

---

# 3. Transactions

## Goal

Track income and spending.

## Requirements

### Transaction Fields

- Date
- Merchant
- Amount
- Category
- Account
- Notes

### Features

- Create transaction
- Edit transaction
- Delete transaction
- Filter by:
  - Date
  - Category
  - Account
  - Merchant

### Categories

Examples:

- Housing
- Utilities
- Transportation
- Food
- Shopping
- Entertainment
- Healthcare
- Income
- Transfer

### Summary Metrics

Display:

- Total Income
- Total Expenses
- Net Cash Flow

### Acceptance Criteria

- Transactions update balances correctly
- Filters work correctly
- Plaid transactions import successfully

---

# 4. Bills

## Goal

Track recurring obligations.

## Requirements

### Bill Fields

- Name
- Amount
- Frequency
- Due Date

### Frequencies

- Weekly
- Biweekly
- Monthly
- Quarterly
- Annually

### Features

- Add bill
- Edit bill
- Delete bill
- Mark paid
- View payment history

### Funding Status

- Funded
- Partially Funded
- Scheduled
- Unfunded

### Acceptance Criteria

- Bills appear in forecast
- Bills affect TAC
- Marking paid advances next due date

---

# 5. Goals

## Goal

Track savings targets.

## Requirements

### Goal Fields

- Name
- Target Amount
- Current Amount
- Target Date

### Features

- Create goal
- Edit goal
- Delete goal
- Deposit funds
- View contribution history

### Calculations

Show:

- Amount Remaining
- Days Remaining
- Paychecks Remaining
- Required Per Paycheck

### Acceptance Criteria

- Deposits update progress immediately
- Goal impacts TAC
- Forecast includes goal funding

---

# 6. Wishlist

## Goal

Plan future purchases.

## Requirements

### Wishlist Fields

- Item Name
- Estimated Cost
- Priority
- Status

### Statuses

- Planned
- Ready To Buy
- Purchased
- Cancelled

### Features

- Create item
- Edit item
- Delete item
- Deposit funds
- View contribution history

### Calculations

Show:

- Amount Saved
- Amount Remaining
- Required Per Paycheck

### Acceptance Criteria

- Wishlist affects TAC
- Forecast includes wishlist contributions
- Purchased items removed from active planning

---

# 7. Paycheck Allocation

## Goal

Show how future paychecks should be distributed.

## Requirements

### Inputs

- Paycheck Amount
- Pay Frequency

### Outputs

Allocate funds toward:

- Bills
- Goals
- Wishlist
- Available Cash

### Views

Display:

- Allocation percentages
- Allocation amounts
- Future paycheck table

### Acceptance Criteria

- Allocation totals always equal paycheck amount
- Warnings displayed if commitments exceed paycheck

---

# 8. Forecast

## Goal

Project future balances.

## Requirements

### Forecast Window

- 90 Days

### Include

- Bills
- Goal Contributions
- Wishlist Contributions
- Paychecks

### Visualizations

- Balance trend chart
- Minimum balance line

### Warnings

- Negative balance
- Low cash
- Missed funding targets

### Acceptance Criteria

- Forecast updates after any financial change
- Forecast reflects future bills accurately

---

# 9. Settings

## Goal

Manage application preferences.

## Requirements

### Paycheck Settings

- Frequency
- Typical Amount

### Threshold Settings

- Minimum Balance
- TAC Warning Level

### Account Settings

- Primary Spending Account

### Acceptance Criteria

- Changes immediately affect calculations

---

# 10. Plaid Integration

## Goal

Automatically import financial data.

## Requirements

### Account Sync

- Import accounts
- Update balances

### Transaction Sync

- Import transactions
- Update modified transactions
- Remove deleted transactions

### Sync Tracking

Store:

- Last Sync Date
- Cursor State

### Acceptance Criteria

- Sync completes without duplicates
- Manual records are preserved
- Multiple syncs are idempotent

---

# Data Model Requirements

## Accounts

- Account
- AccountSnapshot

## Transactions

- Transaction

## Bills

- Bill
- BillPayment

## Goals

- Goal
- GoalDeposit

## Wishlist

- WishlistItem
- WishlistDeposit

## Settings

- Settings

---

# Out of Scope (Post-MVP)

The following are NOT required for Version 1.0:

## AI Features

- AI Financial Coach
- Future Self Simulator
- Purchase Decision Assistant

## Advanced Budgeting

- Category budgets
- Spending alerts
- Push notifications

## Exports

- CSV exports
- PDF reports

## Collaboration

- Shared households
- Multiple users

## Mobile

- iOS app
- Android app

---

# Definition of Done

Fin-Dash Version 1.0 is complete when:

- All core pages are functional
- TAC calculates correctly
- Forecast works correctly
- Bills, Goals, and Wishlist affect TAC
- Plaid sync works
- Data persists correctly
- No critical bugs remain
- A user can fully manage personal finances without spreadsheets

---

# MVP Success Metric

A user should be able to answer:

> "Can I afford this purchase without jeopardizing my bills, savings goals, or future plans?"

within 30 seconds of opening the application.
