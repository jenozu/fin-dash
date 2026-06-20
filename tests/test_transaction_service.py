from datetime import date, timedelta

from services import transaction_service, account_service


def test_get_transactions_df_empty():
    df = transaction_service.get_transactions_df()
    assert df.empty
    assert list(df.columns) == ["id", "Date", "Merchant", "Category", "Amount", "Notes", "Account", "Pending"]


def test_add_transaction_and_fetch():
    transaction_service.add_transaction("Coffee Shop", -5.0, "Coffee", date.today())
    df = transaction_service.get_transactions_df()
    assert len(df) == 1
    assert df.iloc[0]["Merchant"] == "Coffee Shop"


def test_get_transactions_df_filters_by_account():
    account_service.add_account("Checking", "checking", "Spending", "Bank", 100.0)
    acct_id = account_service.get_all_accounts()[0].id
    transaction_service.add_transaction("In Account", -5.0, "Coffee", date.today(), account_id=acct_id)
    transaction_service.add_transaction("No Account", -5.0, "Coffee", date.today())
    df = transaction_service.get_transactions_df(account_id=acct_id)
    assert len(df) == 1
    assert df.iloc[0]["Merchant"] == "In Account"


def test_get_transactions_df_excludes_old_transactions():
    transaction_service.add_transaction("Old", -5.0, "Other", date.today() - timedelta(days=60))
    transaction_service.add_transaction("Recent", -5.0, "Other", date.today())
    df = transaction_service.get_transactions_df(days=30)
    assert len(df) == 1
    assert df.iloc[0]["Merchant"] == "Recent"


def test_get_monthly_spending_and_income():
    transaction_service.add_transaction("Paycheck", 1000.0, "Income", date.today())
    transaction_service.add_transaction("Rent", -500.0, "Home", date.today())
    assert transaction_service.get_monthly_spending() == 500.0
    assert transaction_service.get_monthly_income() == 1000.0


def test_get_spending_by_category():
    transaction_service.add_transaction("Groceries Inc", -50.0, "Groceries", date.today())
    transaction_service.add_transaction("More Groceries", -25.0, "Groceries", date.today())
    transaction_service.add_transaction("Gas Station", -30.0, "Gas", date.today())
    df = transaction_service.get_spending_by_category()
    groceries_row = df[df["Category"] == "Groceries"].iloc[0]
    assert groceries_row["Amount"] == 75.0


def test_update_transaction():
    transaction_service.add_transaction("Coffee Shop", -5.0, "Coffee", date.today())
    txn_id = int(transaction_service.get_transactions_df().iloc[0]["id"])
    transaction_service.update_transaction(txn_id, "Updated Shop", -7.5, "Dining", date.today(), notes="changed")
    df = transaction_service.get_transactions_df()
    assert df.iloc[0]["Merchant"] == "Updated Shop"
    assert df.iloc[0]["Amount"] == -7.5
    assert df.iloc[0]["Notes"] == "changed"


def test_delete_transaction():
    transaction_service.add_transaction("Coffee Shop", -5.0, "Coffee", date.today())
    txn_id = int(transaction_service.get_transactions_df().iloc[0]["id"])
    transaction_service.delete_transaction(txn_id)
    assert transaction_service.get_transactions_df().empty


def test_upsert_plaid_transactions_inserts_added():
    added = [{
        "transaction_id": "ptxn-1",
        "account_id": "plaid-acct-1",
        "amount": 25.0,
        "date": date.today().isoformat(),
        "merchant_name": "Coffee Co",
        "personal_finance_category": {"primary": "FOOD_AND_DRINK"},
        "pending": False,
    }]
    result = transaction_service.upsert_plaid_transactions(added, [], [])
    assert result == {"inserted": 1, "updated": 0, "deleted": 0}
    df = transaction_service.get_transactions_df()
    assert len(df) == 1
    assert df.iloc[0]["Amount"] == -25.0
    assert df.iloc[0]["Category"] == "Dining"


def test_upsert_plaid_transactions_skips_invalid_date():
    added = [{
        "transaction_id": "ptxn-bad-date",
        "account_id": "plaid-acct-1",
        "amount": 25.0,
        "date": "not-a-date",
        "merchant_name": "Bad Date Co",
    }]
    result = transaction_service.upsert_plaid_transactions(added, [], [])
    assert result == {"inserted": 0, "updated": 0, "deleted": 0}
    assert transaction_service.get_transactions_df().empty


def test_upsert_plaid_transactions_does_not_duplicate_existing():
    added = [{
        "transaction_id": "ptxn-1",
        "account_id": "plaid-acct-1",
        "amount": 25.0,
        "date": date.today().isoformat(),
        "merchant_name": "Coffee Co",
    }]
    transaction_service.upsert_plaid_transactions(added, [], [])
    result = transaction_service.upsert_plaid_transactions(added, [], [])
    assert result == {"inserted": 0, "updated": 0, "deleted": 0}
    assert len(transaction_service.get_transactions_df()) == 1


def test_upsert_plaid_transactions_modifies_and_removes():
    added = [{
        "transaction_id": "ptxn-1",
        "account_id": "plaid-acct-1",
        "amount": 25.0,
        "date": date.today().isoformat(),
        "merchant_name": "Coffee Co",
    }]
    transaction_service.upsert_plaid_transactions(added, [], [])

    modified = [{
        "transaction_id": "ptxn-1",
        "amount": 30.0,
        "date": date.today().isoformat(),
        "merchant_name": "Coffee Co Updated",
    }]
    result = transaction_service.upsert_plaid_transactions([], modified, [])
    assert result == {"inserted": 0, "updated": 1, "deleted": 0}
    df = transaction_service.get_transactions_df()
    assert df.iloc[0]["Merchant"] == "Coffee Co Updated"
    assert df.iloc[0]["Amount"] == -30.0

    removed = [{"transaction_id": "ptxn-1"}]
    result = transaction_service.upsert_plaid_transactions([], [], removed)
    assert result == {"inserted": 0, "updated": 0, "deleted": 1}
    assert transaction_service.get_transactions_df().empty
