from datetime import date
from database.database import get_session
from database.models import WishlistItem, WishlistDeposit
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
    if item.planned_purchase_date < date.today():
        return 0.0
    weeks_remaining = max((item.planned_purchase_date - date.today()).days / 7.0, 1.0)
    periods_per_year = PAY_PERIODS_PER_YEAR.get(pay_frequency, 26)
    weeks_per_period = 52.0 / periods_per_year
    return round(remaining / (weeks_remaining / weeks_per_period), 2)


def get_wishlist_committed(pay_frequency="Bi-Weekly"):
    return sum(per_paycheck_for_item(i, pay_frequency) for i in get_active_wishlist())


def update_wishlist_item(item_id, item_name, estimated_cost, current_saved,
                         planned_purchase_date, priority, status, notes):
    session = get_session()
    try:
        item = session.query(WishlistItem).filter(WishlistItem.id == item_id).first()
        if not item:
            return False
        item.item_name = item_name
        item.estimated_cost = float(estimated_cost)
        item.current_saved = float(current_saved)
        item.planned_purchase_date = planned_purchase_date
        item.priority = priority
        item.status = status
        item.notes = notes or ""
        session.commit()
        return True
    finally:
        session.close()


def deposit_to_wishlist_item(item_id, amount, notes=""):
    """Add funds toward a wishlist item and record a deposit entry."""
    session = get_session()
    try:
        item = session.query(WishlistItem).filter(WishlistItem.id == item_id).first()
        if not item:
            return False
        item.current_saved = round(item.current_saved + float(amount), 2)
        session.add(WishlistDeposit(
            item_id=item_id,
            deposit_date=date.today(),
            amount=float(amount),
            notes=notes or "",
        ))
        session.commit()
        return True
    finally:
        session.close()


def get_wishlist_deposit_history(item_id, limit=5):
    session = get_session()
    try:
        return (
            session.query(WishlistDeposit)
            .filter(WishlistDeposit.item_id == item_id)
            .order_by(WishlistDeposit.deposit_date.desc(), WishlistDeposit.id.desc())
            .limit(limit)
            .all()
        )
    finally:
        session.close()
