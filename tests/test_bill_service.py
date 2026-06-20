from datetime import date, timedelta

from services import bill_service, settings_service


def test_get_all_bills_empty():
    assert bill_service.get_all_bills() == []


def test_add_bill_and_get_all_bills():
    bill_service.add_bill("Rent", 1000.0, date.today() + timedelta(days=5), "Monthly")
    bills = bill_service.get_all_bills()
    assert len(bills) == 1
    assert bills[0].bill_name == "Rent"


def test_delete_bill():
    bill_service.add_bill("Rent", 1000.0, date.today() + timedelta(days=5), "Monthly")
    bill_id = bill_service.get_all_bills()[0].id
    bill_service.delete_bill(bill_id)
    assert bill_service.get_all_bills() == []


def test_get_bills_before_paycheck_filters_by_date():
    settings_service.set_setting("next_paycheck_date", (date.today() + timedelta(days=10)).isoformat())
    bill_service.add_bill("InWindow", 50.0, date.today() + timedelta(days=5), "Monthly")
    bill_service.add_bill("OutOfWindow", 50.0, date.today() + timedelta(days=20), "Monthly")
    due = bill_service.get_bills_before_paycheck()
    assert [b.bill_name for b in due] == ["InWindow"]


def test_get_bills_committed_sums_amounts():
    settings_service.set_setting("next_paycheck_date", (date.today() + timedelta(days=10)).isoformat())
    bill_service.add_bill("A", 50.0, date.today() + timedelta(days=2), "Monthly")
    bill_service.add_bill("B", 30.0, date.today() + timedelta(days=3), "Monthly")
    assert bill_service.get_bills_committed() == 80.0


def test_get_monthly_bills_total_each_frequency():
    bill_service.add_bill("Weekly", 100.0, date.today(), "Weekly")
    bill_service.add_bill("BiWeekly", 100.0, date.today(), "Bi-Weekly")
    bill_service.add_bill("Monthly", 100.0, date.today(), "Monthly")
    bill_service.add_bill("Quarterly", 300.0, date.today(), "Quarterly")
    bill_service.add_bill("Annual", 1200.0, date.today(), "Annual")
    total = bill_service.get_monthly_bills_total()
    expected = 100 * 4.33 + 100 * 2.17 + 100 + 300 / 3.0 + 1200 / 12.0
    assert round(total, 2) == round(expected, 2)


def test_mark_bill_paid_records_payment_and_advances_due_date():
    due_date = date.today() + timedelta(days=5)
    bill_service.add_bill("Rent", 1000.0, due_date, "Monthly")
    bill_id = bill_service.get_all_bills()[0].id

    bill_service.mark_bill_paid(bill_id, paid_date=date.today())

    updated_bill = bill_service.get_all_bills()[0]
    assert updated_bill.due_date == due_date + timedelta(days=30)

    history = bill_service.get_payment_history(bill_id)
    assert len(history) == 1
    assert history[0].amount == 1000.0
    assert history[0].due_date == due_date


def test_mark_bill_paid_uses_custom_amount():
    bill_service.add_bill("Utilities", 100.0, date.today(), "Monthly")
    bill_id = bill_service.get_all_bills()[0].id

    bill_service.mark_bill_paid(bill_id, amount=85.50)

    history = bill_service.get_payment_history(bill_id)
    assert history[0].amount == 85.50


def test_get_funding_status_scheduled_when_due_after_paycheck():
    settings_service.set_setting("next_paycheck_date", (date.today() + timedelta(days=5)).isoformat())
    bill_service.add_bill("Future", 50.0, date.today() + timedelta(days=10), "Monthly")
    bill = bill_service.get_all_bills()[0]
    assert bill_service.get_funding_status(bill, 1000.0) == "Scheduled"


def test_get_funding_status_funded_when_balance_covers_amount():
    settings_service.set_setting("next_paycheck_date", (date.today() + timedelta(days=10)).isoformat())
    bill_service.add_bill("Rent", 500.0, date.today() + timedelta(days=2), "Monthly")
    bill = bill_service.get_all_bills()[0]
    assert bill_service.get_funding_status(bill, 1000.0) == "Funded"


def test_get_funding_status_partially_funded():
    settings_service.set_setting("next_paycheck_date", (date.today() + timedelta(days=10)).isoformat())
    bill_service.add_bill("Rent", 500.0, date.today() + timedelta(days=2), "Monthly")
    bill = bill_service.get_all_bills()[0]
    assert bill_service.get_funding_status(bill, 100.0) == "Partially Funded"


def test_get_funding_status_unfunded_when_no_balance():
    settings_service.set_setting("next_paycheck_date", (date.today() + timedelta(days=10)).isoformat())
    bill_service.add_bill("Rent", 500.0, date.today() + timedelta(days=2), "Monthly")
    bill = bill_service.get_all_bills()[0]
    assert bill_service.get_funding_status(bill, 0.0) == "Unfunded"
