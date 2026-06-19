from datetime import date, timedelta

from services import goal_service


def test_get_all_goals_empty():
    assert goal_service.get_all_goals() == []


def test_add_goal_and_get_all_goals():
    goal_service.add_goal("Emergency Fund", 1000.0, 200.0, date.today() + timedelta(days=180))
    goals = goal_service.get_all_goals()
    assert len(goals) == 1
    assert goals[0].goal_name == "Emergency Fund"


def test_delete_goal():
    goal_service.add_goal("Emergency Fund", 1000.0, 200.0, date.today() + timedelta(days=180))
    goal_id = goal_service.get_all_goals()[0].id
    goal_service.delete_goal(goal_id)
    assert goal_service.get_all_goals() == []


def test_per_paycheck_for_goal_returns_zero_when_met():
    goal_service.add_goal("Done", 100.0, 100.0, date.today() + timedelta(days=30))
    goal = goal_service.get_all_goals()[0]
    assert goal_service.per_paycheck_for_goal(goal) == 0.0


def test_per_paycheck_for_goal_returns_zero_when_no_target_date():
    # target_date is NOT NULL in the schema, so simulate a transient/unsaved
    # Goal object (e.g. constructed in memory) rather than persisting it.
    from database.models import Goal
    goal = Goal(goal_name="NoDate", target_amount=100.0, current_amount=0.0, target_date=None)
    assert goal_service.per_paycheck_for_goal(goal) == 0.0


def test_per_paycheck_for_goal_computes_amount():
    target_date = date.today() + timedelta(weeks=4)
    goal_service.add_goal("Vacation", 1000.0, 0.0, target_date)
    goal = goal_service.get_all_goals()[0]
    amount = goal_service.per_paycheck_for_goal(goal, "Bi-Weekly")
    # 4 weeks remaining, bi-weekly = 2 weeks/period -> 2 paychecks left -> 500/check
    assert amount == 500.0


def test_get_goals_committed_sums_all_goals():
    target_date = date.today() + timedelta(weeks=4)
    goal_service.add_goal("A", 1000.0, 0.0, target_date)
    goal_service.add_goal("B", 1000.0, 0.0, target_date)
    total = goal_service.get_goals_committed("Bi-Weekly")
    assert total == 1000.0
