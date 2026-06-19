from datetime import date

from services import account_service


def test_get_all_accounts_empty():
    assert account_service.get_all_accounts() == []


def test_add_account_and_get_spending_balance():
    account_service.add_account("Checking", "checking", "Spending", "Bank", 100.0)
    assert account_service.get_spending_balance() == 100.0
    accounts = account_service.get_all_accounts()
    assert len(accounts) == 1
    assert accounts[0].account_name == "Checking"


def test_get_spending_account_falls_back_when_no_spending_role():
    account_service.add_account("Savings", "savings", "Savings", "Bank", 500.0)
    acct = account_service.get_spending_account()
    assert acct is not None
    assert acct.account_name == "Savings"


def test_get_spending_balance_zero_when_no_accounts():
    assert account_service.get_spending_balance() == 0.0


def test_update_balance_creates_snapshot():
    account_service.add_account("Checking", "checking", "Spending", "Bank", 100.0)
    acct_id = account_service.get_all_accounts()[0].id
    account_service.update_balance(acct_id, 250.0)
    assert account_service.get_spending_balance() == 250.0
    history = account_service.get_balance_history(acct_id)
    assert len(history) == 2
    assert history[-1]["balance"] == 250.0


def test_update_account_details():
    account_service.add_account("Checking", "checking", "Spending", "Bank", 100.0)
    acct_id = account_service.get_all_accounts()[0].id
    account_service.update_account_details(acct_id, "New Name", "Savings", "New Bank")
    acct = account_service.get_all_accounts()[0]
    assert acct.account_name == "New Name"
    assert acct.account_role == "Savings"
    assert acct.institution_name == "New Bank"


def test_deactivate_account_excludes_from_list():
    account_service.add_account("Checking", "checking", "Spending", "Bank", 100.0)
    acct_id = account_service.get_all_accounts()[0].id
    account_service.deactivate_account(acct_id)
    assert account_service.get_all_accounts() == []


def test_upsert_plaid_accounts_creates_and_updates():
    plaid_accounts = [{
        "account_id": "plaid-1",
        "name": "Plaid Checking",
        "type": "depository",
        "subtype": "checking",
        "balances": {"current": 100.0, "available": 90.0},
    }]
    result = account_service.upsert_plaid_accounts(plaid_accounts, "item-1")
    assert result == {"created": 1, "updated": 0}
    accounts = account_service.get_all_accounts()
    assert len(accounts) == 1
    assert accounts[0].account_role == "Spending"

    plaid_accounts[0]["balances"]["current"] = 200.0
    result = account_service.upsert_plaid_accounts(plaid_accounts, "item-1")
    assert result == {"created": 0, "updated": 1}
    assert account_service.get_all_accounts()[0].current_balance == 200.0
