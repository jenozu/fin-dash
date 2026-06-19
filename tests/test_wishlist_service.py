from datetime import date, timedelta

from services import wishlist_service


def test_get_active_wishlist_empty():
    assert wishlist_service.get_active_wishlist() == []


def test_add_item_appears_in_active_wishlist():
    wishlist_service.add_wishlist_item(
        "Laptop", 1500.0, 0.0, date.today() + timedelta(days=60), "High", "Planning"
    )
    items = wishlist_service.get_active_wishlist()
    assert len(items) == 1
    assert items[0].item_name == "Laptop"


def test_purchased_items_excluded_from_active_wishlist():
    wishlist_service.add_wishlist_item(
        "Laptop", 1500.0, 1500.0, date.today(), "High", "Purchased"
    )
    assert wishlist_service.get_active_wishlist() == []


def test_cancelled_items_excluded_from_active_wishlist():
    wishlist_service.add_wishlist_item(
        "Laptop", 1500.0, 0.0, date.today(), "High", "Cancelled"
    )
    assert wishlist_service.get_active_wishlist() == []


def test_delete_wishlist_item():
    wishlist_service.add_wishlist_item(
        "Laptop", 1500.0, 0.0, date.today() + timedelta(days=60), "High", "Planning"
    )
    item_id = wishlist_service.get_active_wishlist()[0].id
    wishlist_service.delete_wishlist_item(item_id)
    assert wishlist_service.get_active_wishlist() == []


def test_per_paycheck_for_item_zero_when_no_purchase_date():
    wishlist_service.add_wishlist_item("NoDate", 100.0, 0.0, None, "Low", "Idea")
    item = wishlist_service.get_active_wishlist()[0]
    assert wishlist_service.per_paycheck_for_item(item) == 0.0


def test_per_paycheck_for_item_zero_when_fully_saved():
    wishlist_service.add_wishlist_item(
        "Done", 100.0, 100.0, date.today() + timedelta(days=30), "Low", "Saving"
    )
    item = wishlist_service.get_active_wishlist()[0]
    assert wishlist_service.per_paycheck_for_item(item) == 0.0


def test_per_paycheck_for_item_computes_amount():
    target_date = date.today() + timedelta(weeks=4)
    wishlist_service.add_wishlist_item("Camera", 800.0, 0.0, target_date, "Medium", "Saving")
    item = wishlist_service.get_active_wishlist()[0]
    amount = wishlist_service.per_paycheck_for_item(item, "Bi-Weekly")
    assert amount == 400.0


def test_get_wishlist_committed_sums_items():
    target_date = date.today() + timedelta(weeks=4)
    wishlist_service.add_wishlist_item("A", 800.0, 0.0, target_date, "Medium", "Saving")
    wishlist_service.add_wishlist_item("B", 800.0, 0.0, target_date, "Medium", "Saving")
    assert wishlist_service.get_wishlist_committed("Bi-Weekly") == 800.0
