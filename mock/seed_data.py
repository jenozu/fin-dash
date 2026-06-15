from datetime import date, timedelta
from database.database import get_session
from database.models import Account, AccountSnapshot, Transaction, Bill, Goal, WishlistItem, Setting


def seed_if_empty():
    session = get_session()
    try:
        if session.query(Account).count() > 0:
            return
        today = date.today()
        accounts = _seed_accounts(session)
        session.flush()
        _seed_snapshots(session, accounts, today)
        _seed_bills(session, today)
        _seed_goals(session, today)
        _seed_wishlist(session, today)
        _seed_settings(session, today)
        _seed_transactions(session, today, accounts[0])
        session.commit()
    finally:
        session.close()


def _seed_accounts(session):
    accounts = [
        Account(
            account_name="First Platypus Checking",
            account_type="depository",
            account_subtype="checking",
            account_role="Spending",
            current_balance=3247.58,
            available_balance=3247.58,
            institution_name="First Platypus Bank",
            is_active=True,
        ),
        Account(
            account_name="Bills Reserve",
            account_type="depository",
            account_subtype="checking",
            account_role="Bills Reserve",
            current_balance=2400.00,
            available_balance=2400.00,
            institution_name="First Platypus Bank",
            is_active=True,
        ),
        Account(
            account_name="High Yield Savings",
            account_type="depository",
            account_subtype="savings",
            account_role="Savings",
            current_balance=1260.00,
            available_balance=1260.00,
            institution_name="First Platypus Bank",
            is_active=True,
        ),
    ]
    session.add_all(accounts)
    return accounts


def _seed_snapshots(session, accounts, today):
    for account in accounts:
        session.add(AccountSnapshot(
            account_id=account.id,
            snapshot_date=today,
            balance=account.current_balance,
            notes="Initial seed balance",
        ))


def _seed_bills(session, today):
    session.add_all([
        Bill(bill_name="Rent", amount=1200.00, due_date=today + timedelta(days=3), frequency="Monthly"),
        Bill(bill_name="Phone", amount=85.00, due_date=today + timedelta(days=8), frequency="Monthly"),
        Bill(bill_name="Internet", amount=60.00, due_date=today + timedelta(days=13), frequency="Monthly"),
        Bill(bill_name="Netflix", amount=15.99, due_date=today + timedelta(days=19), frequency="Monthly"),
        Bill(bill_name="Car Insurance", amount=142.00, due_date=today + timedelta(days=19), frequency="Monthly"),
    ])


def _seed_goals(session, today):
    session.add_all([
        Goal(
            goal_name="Emergency Fund",
            target_amount=5000.00,
            current_amount=1247.00,
            target_date=date(today.year + 1, 1, 1),
            notes="3 to 6 months of expenses",
        ),
        Goal(
            goal_name="Vacation Fund",
            target_amount=2500.00,
            current_amount=412.00,
            target_date=date(today.year, 12, 1),
            notes="Annual beach trip",
        ),
        Goal(
            goal_name="New Car Fund",
            target_amount=8000.00,
            current_amount=650.00,
            target_date=date(today.year + 1, 6, 1),
            notes="Down payment",
        ),
    ])


def _seed_wishlist(session, today):
    session.add_all([
        WishlistItem(
            item_name="Laser Engraver",
            estimated_cost=500.00,
            current_saved=100.00,
            planned_purchase_date=today + timedelta(days=80),
            priority="High",
            status="Saving",
            notes="xTool D1 Pro",
        ),
        WishlistItem(
            item_name="New Laptop",
            estimated_cost=1200.00,
            current_saved=300.00,
            planned_purchase_date=today + timedelta(days=200),
            priority="Medium",
            status="Saving",
            notes="For work and side projects",
        ),
        WishlistItem(
            item_name="Bike Upgrade",
            estimated_cost=350.00,
            current_saved=0.00,
            planned_purchase_date=today + timedelta(days=111),
            priority="Low",
            status="Planning",
            notes="New wheels and components",
        ),
        WishlistItem(
            item_name="Standing Desk",
            estimated_cost=600.00,
            current_saved=150.00,
            planned_purchase_date=today + timedelta(days=142),
            priority="Medium",
            status="Saving",
            notes="Ergonomic home office upgrade",
        ),
    ])


def _seed_settings(session, today):
    days_until_friday = (4 - today.weekday()) % 7
    if days_until_friday == 0:
        days_until_friday = 7
    next_paycheck = today + timedelta(days=days_until_friday)
    session.add_all([
        Setting(setting_name="pay_frequency", setting_value="Bi-Weekly"),
        Setting(setting_name="average_paycheck", setting_value="1800"),
        Setting(setting_name="next_paycheck_date", setting_value=str(next_paycheck)),
        Setting(setting_name="tac_alert_threshold", setting_value="500"),
        Setting(setting_name="min_balance", setting_value="500"),
        Setting(setting_name="plaid_access_token", setting_value=""),
        Setting(setting_name="plaid_item_id", setting_value=""),
    ])


def _seed_transactions(session, today, spending_account):
    raw = [
        ("Direct Deposit", "Income", 1800.00, 1),
        ("Direct Deposit", "Income", 1800.00, 15),
        ("Publix", "Groceries", -67.43, 2),
        ("Walmart", "Groceries", -89.12, 9),
        ("Whole Foods", "Groceries", -54.21, 17),
        ("Publix", "Groceries", -72.30, 23),
        ("Shell Gas Station", "Gas", -48.00, 3),
        ("BP", "Gas", -52.50, 10),
        ("Shell Gas Station", "Gas", -51.00, 24),
        ("Chipotle", "Dining", -14.75, 4),
        ("Chick-fil-A", "Dining", -11.50, 6),
        ("Panera Bread", "Dining", -13.25, 12),
        ("Olive Garden", "Dining", -42.80, 18),
        ("Dominos", "Dining", -26.47, 25),
        ("Chick-fil-A", "Dining", -10.89, 28),
        ("Starbucks", "Coffee", -6.75, 5),
        ("Dunkin", "Coffee", -5.20, 11),
        ("Starbucks", "Coffee", -7.25, 19),
        ("Amazon", "Shopping", -34.99, 7),
        ("Amazon", "Shopping", -67.50, 16),
        ("Target", "Shopping", -45.60, 22),
        ("Dollar Tree", "Shopping", -15.00, 29),
        ("Spotify", "Subscriptions", -9.99, 8),
        ("Netflix", "Subscriptions", -15.99, 8),
        ("Apple App Store", "Subscriptions", -4.99, 20),
        ("AMC Theaters", "Entertainment", -28.00, 13),
        ("Planet Fitness", "Health", -24.99, 1),
        ("CVS Pharmacy", "Health", -18.40, 14),
        ("Home Depot", "Home", -89.50, 21),
        ("Venmo Transfer", "Transfer", -50.00, 26),
    ]
    for merchant, category, amount, days_ago in raw:
        session.add(Transaction(
            merchant=merchant,
            amount=amount,
            category=category,
            transaction_date=today - timedelta(days=days_ago),
            account_id=spending_account.id,
            is_pending=False,
        ))
