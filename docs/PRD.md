# Product Requirements Document (PRD)

# Money Command Center

Version: 2.0

Owner: Andel O'Bryan

Status: Source of Truth

Platform: Desktop Web Application

Primary Stack:

* Python
* Streamlit
* SQLite
* SQLAlchemy
* Plaid API
* Plotly

---

# Executive Summary

Money Command Center is a personal financial planning platform that combines banking visibility, transaction tracking, bill planning, savings goals, wishlist management, paycheck allocation, and cash flow forecasting into a single command center.

Unlike traditional budgeting applications, the primary purpose is not expense tracking.

The primary purpose is helping users understand:

* What money is already committed
* What money is available
* What future purchases are being planned
* How spending decisions impact future goals
* How much money can safely be spent today

The application should become a financial operating system for personal decision-making.

---

# Problem Statement

Most banking applications only show balances and transactions.

This creates a common problem:

A user sees $2,500 in a bank account and assumes they have $2,500 available.

In reality:

* Bills are due later
* Savings goals are underfunded
* Planned purchases have not been accounted for
* Future obligations are invisible

Users need a system that converts account balances into actionable financial information.

---

# Product Philosophy

Traditional Banking:

> What happened?

Money Command Center:

> What happens next?

The application focuses on future planning rather than historical reporting.

---

# Core Metric

## True Available Cash (TAC)

This is the most important metric in the entire application.

Formula:

Current Balance

Minus Upcoming Bills

Minus Goal Allocations

Minus Wishlist Allocations

Equals

True Available Cash

Example:

Balance: $2,500

Bills: $1,500

Goals: $300

Wishlist: $200

TAC: $500

The user should always know:

> How much can I safely spend right now?

without harming future goals.

---

# Target User

## Primary User

Andel O'Bryan

Characteristics:

* Working professional
* Paid on recurring schedule
* Multiple savings objectives
* Future purchases being planned
* Comfortable with technology
* Wants proactive financial planning

## Future Audience

* Individuals
* Families
* Financial coaching clients
* Financial consultants

---

# MVP Goal

A user should be able to open the dashboard and immediately answer:

1. How much money do I have?
2. What bills are coming up?
3. What am I saving for?
4. What purchases am I planning?
5. How much should I save from my next paycheck?
6. How much money is already committed?
7. How much can I safely spend today?

without opening their banking application.

---

# Functional Requirements

# Module 1: Accounts

## Purpose

Display connected bank accounts and balances.

## Features

Display:

* Account Name
* Account Type
* Account Role
* Current Balance
* Available Balance
* Last Updated

Account Roles:

* Spending
* Bills Reserve
* Savings
* Investment

Future:

* Multiple institutions
* Credit cards
* Loans

---

# Module 2: Transactions

## Purpose

Provide visibility into spending activity.

## Features

Transaction Table

Fields:

* Date
* Merchant
* Amount
* Category
* Account
* Notes

Functions:

* Search
* Sort
* Filter
* Date Range Selection
* Account Filtering
* Manual Add/Edit/Delete

---

# Module 3: Bill Manager

## Purpose

Track future financial obligations.

## Bill Fields

* Bill Name
* Amount
* Due Date
* Frequency
* Notes
* Funding Status

Supported Frequencies:

* Weekly
* Bi-Weekly
* Monthly
* Quarterly
* Annual

Metrics:

* Monthly Bills Total
* Upcoming Bills
* Bills Due Within 30 Days

---

# Module 4: Savings Goals

## Purpose

Track long-term financial objectives.

## Goal Fields

* Goal Name
* Target Amount
* Current Amount
* Target Date
* Notes

Examples:

* Emergency Fund
* Vacation
* House Down Payment
* Vehicle Purchase

Metrics:

* Progress %
* Remaining Amount
* Time Remaining

---

# Module 5: Wishlist Planner

## Purpose

Track future purchases intentionally.

## Wishlist Fields

* Item Name
* Estimated Cost
* Priority
* Notes
* Planned Purchase Date
* Current Saved Amount
* Status

Statuses:

* Idea
* Planning
* Saving
* Ready To Buy
* Purchased
* Cancelled

---

# Module 6: Savings Calculator

## Purpose

Determine required savings contributions.

Formula:

Remaining Amount

÷

Remaining Time

Outputs:

* Weekly Savings Required
* Monthly Savings Required
* Per-Paycheck Savings Required

Example:

Item Cost: $500

Current Saved: $100

Remaining: $400

Time Remaining: 8 Weeks

Required Savings:

$50/week

---

# Module 7: Paycheck Allocation Planner

## Purpose

Show where every paycheck should go.

Inputs:

* Pay Frequency
* Average Paycheck

Outputs:

* Bills Allocation
* Goal Allocation
* Wishlist Allocation
* Available Spending

Example:

Paycheck: $1,800

Bills: $800

Goals: $300

Wishlist: $200

Available Spending: $500

---

# Module 8: Forecast Engine

## Purpose

Predict future financial position.

Displays:

* Upcoming Bills
* Upcoming Paychecks
* Goal Contributions
* Wishlist Contributions
* Projected Cash Position
* Projected TAC

Forecast Period:

* 30 Days
* 60 Days
* 90 Days

---

# Module 9: Plaid Integration

## Purpose

Import real financial data.

Requirements:

* Connect financial institution
* Sync accounts
* Sync balances
* Sync transactions
* Incremental transaction updates
* Disconnect institution

Security:

* Never store credentials
* Use Plaid access tokens only
* Store secrets in environment variables

---

# Dashboard Requirements

## Primary Cards

* Current Balance
* True Available Cash
* Monthly Spending
* Monthly Income
* Net Cash Flow
* Upcoming Bills
* Goal Progress
* Wishlist Progress

## Charts

* Spending By Category
* Monthly Spending Trend
* Goal Progress
* Wishlist Progress
* Forecast Trend

---

# Database Requirements

Accounts

* id
* account_name
* account_type
* account_role
* account_subtype
* current_balance
* available_balance
* is_active

Transactions

* id
* account_id
* merchant
* amount
* category
* notes
* transaction_date

Bills

* id
* bill_name
* amount
* due_date
* frequency
* notes

Goals

* id
* goal_name
* target_amount
* current_amount
* target_date

Wishlist

* id
* item_name
* estimated_cost
* current_saved
* planned_purchase_date
* priority
* status

AccountSnapshots

* id
* account_id
* balance
* snapshot_date

Settings

* id
* setting_name
* setting_value

---

# Security Requirements

Must:

* Use Plaid authentication
* Store tokens securely
* Use environment variables
* Allow account disconnect
* Protect financial data

Must Not:

* Store bank usernames
* Store bank passwords
* Store security questions
* Store banking login credentials

---

# Out of Scope (MVP)

The following are NOT required for MVP completion:

* Mobile applications
* Multi-user support
* Family accounts
* Investment management
* Cryptocurrency support
* Credit score monitoring
* Bill payments
* Automatic transfers
* AI financial coaching
* Opportunity Cost Engine
* Future Self Decision Assistant
* Spending alerts
* Budget alerts

These belong in future releases.

---

# Post-MVP Roadmap

## Version 2

* Spending alerts
* Budget alerts
* Category improvements
* CSV exports
* Recurring transaction templates

## Version 3

* Opportunity Cost Engine
* Purchase impact analysis
* Financial runway calculations

## Version 4

* AI Financial Coach
* Future Self Decision Assistant
* Purchase scoring system

## Version 5

* Family finances
* Shared planning
* Coaching portal
* Client dashboards

---

# MVP Acceptance Criteria

The MVP is complete when:

* User can connect a bank account.
* Transactions import successfully.
* Bills can be tracked.
* Savings goals can be tracked.
* Wishlist items can be tracked.
* Savings requirements are calculated.
* Forecast page functions correctly.
* Paycheck allocation planner functions correctly.
* True Available Cash is calculated correctly.

---

# Definition of Done

The product is considered MVP complete when a user can answer the following questions in under 60 seconds:

1. How much money do I have?
2. What money is already committed?
3. What bills are coming up?
4. What am I saving for?
5. What purchases am I planning?
6. How much should I save from my next paycheck?
7. How much can I safely spend today?

without opening their banking app.
