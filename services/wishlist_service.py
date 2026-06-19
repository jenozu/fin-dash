from datetime import date
from database.database import get_session
from database.models import WishlistItem
from config.constants import PAY_PERIODS_PER_YEAR


def get_active_wishlist():
    session = get_session()
    try:
        return (
            session.query(WishlistItem)
            .filter(WishlistItem.status.notin_(["Purchased", "Cancelled"]))
            .all()
        )
    finally:
        session.close()


def per_paycheck_for_item(item, pay_frequency="Bi-Weekly"):
    remaining = item.estimated_cost - item.current_saved
    if remaining <= 0 or not item.planned_purchase_date:
        return 0.0
    weeks_remaining = max((item.planned_purchase_date - date.today()).days / 7.0, 1.0)
    periods_per_year = PAY_PERIODS_PER_YEAR.get(pay_frequency, 26)
    weeks_per_period = 52.0 / periods_per_year
    return round(remaining / (weeks_remaining / weeks_per_period), 2)


def get_wishlist_committed(pay_frequency="Bi-Weekly"):
    return sum(per_paycheck_for_item(i, pay_frequency) for i in get_active_wishlist())


def add_wishlist_item(item_name, estimated_cost, current_saved, planned_purchase_date, priority, status, notes=None):
    session = get_session()
    try:
        session.add(WishlistItem(
            item_name=item_name, estimated_cost=estimated_cost, current_saved=current_saved,
            planned_purchase_date=planned_purchase_date, priority=priority,
            status=status, notes=notes,
        ))
        session.commit()
    finally:
        session.close()


def delete_wishlist_item(item_id):
    session = get_session()
    try:
        session.query(WishlistItem).filter(WishlistItem.id == item_id).delete()
        session.commit()
    finally:
        session.close()
