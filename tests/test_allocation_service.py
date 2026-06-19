from datetime import date, timedelta

from services import allocation_service, account_service, bill_service, settings_service


def test_get_current_balance_zero_when_no_accounts():
    assert allocation_service.get_current_balance() == 0.0


def test_calculate_true_available_cash():
    account_service.add_account("Checking", "checking", "Spending", "Bank", 1000.0)
    settings_service.set_setting("next_paycheck_date", (date.today() + timedelta(days=10)).isoformat())
    bill_service.add_bill("Rent", 200.0, date.today() + timedelta(days=5), "Monthly")
    result = allocation_service.calculate_true_available_cash()
    assert result["balance"] == 1000.0
    assert result["bills_committed"] == 200.0
    assert result["true_available"] == 800.0


def test_calculate_paycheck_allocation():
    settings_service.set_setting("pay_frequency", "Bi-Weekly")
    settings_service.set_setting("average_paycheck", "1000")
    bill_service.add_bill("Rent", 100.0, date.today(), "Monthly")
    result = allocation_service.calculate_paycheck_allocation()
    assert result["paycheck"] == 1000.0
    # monthly bills total = 100, *12/26 periods per year
    assert result["bills"] == round(100.0 * 12.0 / 26, 2)
    assert result["available"] == round(1000.0 - result["bills"], 2)
