from unittest.mock import patch, MagicMock

import pytest

from services import plaid_service


def test_map_category_uses_primary_pfc():
    txn = {"personal_finance_category": {"primary": "FOOD_AND_DRINK"}}
    assert plaid_service.map_category(txn) == "Dining"


def test_map_category_falls_back_to_legacy_category():
    txn = {"category": ["Travel", "Airlines"]}
    assert plaid_service.map_category(txn) == "Travel"


def test_map_category_defaults_to_other():
    txn = {}
    assert plaid_service.map_category(txn) == "Other"


def test_map_category_legacy_coffee_vs_dining():
    assert plaid_service.map_category({"category": ["Food and Drink", "Coffee Shop"]}) == "Coffee"
    assert plaid_service.map_category({"category": ["Food and Drink", "Restaurants"]}) == "Dining"


def test_guess_account_role_checking():
    assert plaid_service.guess_account_role({"subtype": "checking"}) == "Spending"


def test_guess_account_role_savings():
    assert plaid_service.guess_account_role({"subtype": "savings"}) == "Savings"


def test_guess_account_role_investment():
    assert plaid_service.guess_account_role({"type": "investment", "subtype": "brokerage"}) == "Investment"


def test_guess_account_role_unknown_defaults_other():
    assert plaid_service.guess_account_role({"subtype": "credit card"}) == "Other"


def test_is_configured_false_without_credentials():
    with patch.object(plaid_service, "PLAID_CLIENT_ID", ""), patch.object(plaid_service, "PLAID_SECRET", ""):
        assert plaid_service.is_configured() is False


def test_post_raises_when_not_configured():
    with patch.object(plaid_service, "PLAID_CLIENT_ID", ""), patch.object(plaid_service, "PLAID_SECRET", ""):
        with pytest.raises(RuntimeError, match="not configured"):
            plaid_service._post("/sandbox/public_token/create", {})


def test_post_raises_on_api_error_response():
    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.json.return_value = {"error_code": "BAD_REQUEST", "error_message": "nope"}
    with patch.object(plaid_service, "PLAID_CLIENT_ID", "id"), \
         patch.object(plaid_service, "PLAID_SECRET", "secret"), \
         patch("services.plaid_service.requests.post", return_value=mock_resp):
        with pytest.raises(RuntimeError, match="BAD_REQUEST"):
            plaid_service._post("/some/endpoint", {})


def test_post_raises_clear_error_on_non_json_response():
    mock_resp = MagicMock()
    mock_resp.status_code = 503
    mock_resp.json.side_effect = ValueError("not json")
    mock_resp.raise_for_status.side_effect = Exception("HTTP 503")
    with patch.object(plaid_service, "PLAID_CLIENT_ID", "id"), \
         patch.object(plaid_service, "PLAID_SECRET", "secret"), \
         patch("services.plaid_service.requests.post", return_value=mock_resp):
        with pytest.raises(Exception):
            plaid_service._post("/some/endpoint", {})


def test_post_returns_data_on_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"public_token": "abc"}
    with patch.object(plaid_service, "PLAID_CLIENT_ID", "id"), \
         patch.object(plaid_service, "PLAID_SECRET", "secret"), \
         patch("services.plaid_service.requests.post", return_value=mock_resp):
        result = plaid_service._post("/some/endpoint", {})
        assert result == {"public_token": "abc"}
