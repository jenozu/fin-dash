from datetime import date, timedelta
import pandas as pd
from database.database import get_session
from database.models import Budget
from services.transaction_service import get_spending_by_category


def get_all_budgets():
    session = get_session()
    try:
        return (
            session.query(Budget)
            .filter(Budget.is_active == True)
            .order_by(Budget.category)
            .all()
        )
    finally:
        session.close()


def add_budget(category, monthly_limit):
    session = get_session()
    try:
        existing = session.query(Budget).filter(Budget.category == category).first()
        if existing:
            existing.monthly_limit = float(monthly_limit)
            existing.is_active = True
        else:
            session.add(Budget(category=category, monthly_limit=float(monthly_limit)))
        session.commit()
        return True
    finally:
        session.close()


def update_budget(budget_id, monthly_limit):
    session = get_session()
    try:
        budget = session.query(Budget).filter(Budget.id == budget_id).first()
        if not budget:
            return False
        budget.monthly_limit = float(monthly_limit)
        session.commit()
        return True
    finally:
        session.close()


def delete_budget(budget_id):
    session = get_session()
    try:
        session.query(Budget).filter(Budget.id == budget_id).delete()
        session.commit()
        return True
    finally:
        session.close()


def get_budget_vs_actual(days=30):
    """Returns DataFrame: category, monthly_limit, actual, remaining, pct_used."""
    budgets = get_all_budgets()
    if not budgets:
        return pd.DataFrame(columns=["category", "monthly_limit", "actual", "remaining", "pct_used"])

    actual_df = get_spending_by_category(days)
    actual_map = (
        dict(zip(actual_df["Category"], actual_df["Amount"]))
        if not actual_df.empty
        else {}
    )

    rows = []
    for b in budgets:
        actual = actual_map.get(b.category, 0.0)
        remaining = b.monthly_limit - actual
        pct_used = (actual / b.monthly_limit) if b.monthly_limit > 0 else 0.0
        rows.append({
            "category": b.category,
            "monthly_limit": b.monthly_limit,
            "actual": actual,
            "remaining": remaining,
            "pct_used": pct_used,
        })

    return pd.DataFrame(rows)


def get_over_budget_categories(days=30):
    """Returns list of dicts for categories where actual > monthly_limit."""
    df = get_budget_vs_actual(days)
    if df.empty:
        return []
    over = df[df["actual"] > df["monthly_limit"]]
    return over.to_dict("records")
