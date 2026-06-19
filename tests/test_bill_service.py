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
