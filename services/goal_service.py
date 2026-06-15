from datetime import date
from database.database import get_session
from database.models import Goal, GoalDeposit
from config.constants import PAY_PERIODS_PER_YEAR


def get_all_goals():
    session = get_session()
    try:
        return session.query(Goal).all()
    finally:
        session.close()


def per_paycheck_for_goal(goal, pay_frequency="Bi-Weekly"):
    remaining = goal.target_amount - goal.current_amount
    if remaining <= 0 or not goal.target_date:
        return 0.0
    if goal.target_date < date.today():
        return 0.0
    weeks_remaining = max((goal.target_date - date.today()).days / 7.0, 1.0)
    periods_per_year = PAY_PERIODS_PER_YEAR.get(pay_frequency, 26)
    weeks_per_period = 52.0 / periods_per_year
    return round(remaining / (weeks_remaining / weeks_per_period), 2)


def get_goals_committed(pay_frequency="Bi-Weekly"):
    return sum(per_paycheck_for_goal(g, pay_frequency) for g in get_all_goals())


def update_goal(goal_id, goal_name, target_amount, current_amount, target_date, notes):
    session = get_session()
    try:
        goal = session.query(Goal).filter(Goal.id == goal_id).first()
        if not goal:
            return False
        goal.goal_name = goal_name
        goal.target_amount = float(target_amount)
        goal.current_amount = float(current_amount)
        goal.target_date = target_date
        goal.notes = notes or ""
        session.commit()
        return True
    finally:
        session.close()


def deposit_to_goal(goal_id, amount, notes=""):
    """Add funds to a goal and record a deposit entry."""
    session = get_session()
    try:
        goal = session.query(Goal).filter(Goal.id == goal_id).first()
        if not goal:
            return False
        goal.current_amount = round(goal.current_amount + float(amount), 2)
        session.add(GoalDeposit(
            goal_id=goal_id,
            deposit_date=date.today(),
            amount=float(amount),
            notes=notes or "",
        ))
        session.commit()
        return True
    finally:
        session.close()


def get_goal_deposit_history(goal_id, limit=5):
    session = get_session()
    try:
        return (
            session.query(GoalDeposit)
            .filter(GoalDeposit.goal_id == goal_id)
            .order_by(GoalDeposit.deposit_date.desc(), GoalDeposit.id.desc())
            .limit(limit)
            .all()
        )
    finally:
        session.close()
