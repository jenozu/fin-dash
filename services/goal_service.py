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
    weeks_remaining = max((goal.target_date - date.today()).days / 7.0, 1.0)
    periods_per_year = PAY_PERIODS_PER_YEAR.get(pay_frequency, 26)
    weeks_per_period = 52.0 / periods_per_year
    return round(remaining / (weeks_remaining / weeks_per_period), 2)


def get_goals_committed(pay_frequency="Bi-Weekly"):
    return sum(per_paycheck_for_goal(g, pay_frequency) for g in get_all_goals())


def add_goal(goal_name, target_amount, current_amount, target_date, notes=None):
    session = get_session()
    try:
        session.add(Goal(
            goal_name=goal_name, target_amount=target_amount,
            current_amount=current_amount, target_date=target_date, notes=notes,
        ))
        session.commit()
    finally:
        session.close()


def delete_goal(goal_id):
    session = get_session()
    try:
        session.query(Goal).filter(Goal.id == goal_id).delete()
        session.commit()
    finally:
        session.close()


def add_goal_deposit(goal_id, amount, deposit_date=None):
    """Record a deposit toward a goal and update its current amount."""
    deposit_date = deposit_date or date.today()
    session = get_session()
    try:
        goal = session.query(Goal).filter(Goal.id == goal_id).first()
        if not goal:
            return
        session.add(GoalDeposit(goal_id=goal.id, amount=amount, deposit_date=deposit_date))
        goal.current_amount += amount
        session.commit()
    finally:
        session.close()


def get_deposit_history(goal_id):
    session = get_session()
    try:
        return (
            session.query(GoalDeposit)
            .filter(GoalDeposit.goal_id == goal_id)
            .order_by(GoalDeposit.deposit_date.desc())
            .all()
        )
    finally:
        session.close()
