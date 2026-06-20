"""
Plaid REST API client for Sandbox environment.
Uses requests directly — no SDK required.
"""
import requests
from datetime import datetime
from config.settings import PLAID_CLIENT_ID, PLAID_SECRET, PLAID_ENV

PLAID_BASE_URLS = {
    "sandbox": "https://sandbox.plaid.com",
    "development": "https://development.plaid.com",
    "production": "https://production.plaid.com",
}

# First Platypus Bank sandbox institution ID
SANDBOX_INSTITUTION_ID = "ins_109508"

# Plaid personal_finance_category → our TRANSACTION_CATEGORIES mapping
CATEGORY_MAP = {
    "INCOME": "Income",
    "TRANSFER_IN": "Transfer",
    "TRANSFER_OUT": "Transfer",
    "LOAN_PAYMENTS": "Other",
    "BANK_FEES": "Other",
    "ENTERTAINMENT": "Entertainment",
    "FOOD_AND_DRINK": "Dining",
    "GENERAL_MERCHANDISE": "Shopping",
    "HOME_IMPROVEMENT": "Home",
    "MEDICAL": "Health",
    "PERSONAL_CARE": "Health",
    "GENERAL_SERVICES": "Other",
    "GOVERNMENT_AND_NON_PROFIT": "Other",
    "TRANSPORTATION": "Gas",
    "TRAVEL": "Travel",
    "RENT_AND_UTILITIES": "Utilities",
    "SUBSCRIPTION": "Subscriptions",
}


def _is_configured():
    return bool(PLAID_CLIENT_ID and PLAID_SECRET)


def _base_url():
    env = PLAID_ENV if PLAID_ENV in PLAID_BASE_URLS else "sandbox"
    return PLAID_BASE_URLS[env]


def _post(endpoint: str, body: dict) -> dict:
    """Authenticated POST to Plaid API. Raises on HTTP or API errors."""
    if not _is_configured():
        raise RuntimeError("Plaid credentials not configured. Set PLAID_CLIENT_ID and PLAID_SECRET in .env")
    payload = {"client_id": PLAID_CLIENT_ID, "secret": PLAID_SECRET, **body}
    resp = requests.post(f"{_base_url()}{endpoint}", json=payload, timeout=30)
    try:
        data = resp.json()
    except ValueError:
        resp.raise_for_status()
        raise RuntimeError(f"Plaid API returned a non-JSON response (status {resp.status_code})")
    if resp.status_code != 200:
        error_code = data.get("error_code", "UNKNOWN")
        error_msg = data.get("error_message", resp.text)
        raise RuntimeError(f"Plaid API error [{error_code}]: {error_msg}")
    return data


def is_configured():
    return _is_configured()


def create_sandbox_token(institution_id: str = SANDBOX_INSTITUTION_ID) -> str:
    """Create a sandbox public_token for First Platypus Bank (no Link UI needed)."""
    data = _post("/sandbox/public_token/create", {
        "institution_id": institution_id,
        "initial_products": ["transactions"],
        "options": {"override_username": "user_good", "override_password": "pass_good"},
    })
    return data["public_token"]


def exchange_public_token(public_token: str) -> dict:
    """Exchange a public_token for an access_token + item_id."""
    data = _post("/item/public_token/exchange", {"public_token": public_token})
    return {"access_token": data["access_token"], "item_id": data["item_id"]}


def get_accounts(access_token: str) -> list:
    """Return list of account dicts from Plaid."""
    data = _post("/accounts/get", {"access_token": access_token})
    return data.get("accounts", [])


def sync_transactions(access_token: str, cursor: str = None) -> dict:
    """
    Fetch transaction updates using /transactions/sync.
    Returns {added, modified, removed, next_cursor, has_more}.
    Paginates automatically until has_more is False.
    """
    added, modified, removed = [], [], []
    next_cursor = cursor

    while True:
        body = {"access_token": access_token, "count": 500}
        if next_cursor:
            body["cursor"] = next_cursor

        data = _post("/transactions/sync", body)
        added.extend(data.get("added", []))
        modified.extend(data.get("modified", []))
        removed.extend(data.get("removed", []))
        next_cursor = data.get("next_cursor", "")

        if not data.get("has_more", False):
            break

    return {
        "added": added,
        "modified": modified,
        "removed": removed,
        "next_cursor": next_cursor,
    }


def map_category(plaid_txn: dict) -> str:
    """Map Plaid personal_finance_category to our category list."""
    pfc = plaid_txn.get("personal_finance_category") or {}
    primary = (pfc.get("primary") or "").upper()
    if primary in CATEGORY_MAP:
        return CATEGORY_MAP[primary]
    # Fallback: check legacy category list
    legacy = plaid_txn.get("category") or []
    legacy_str = " ".join(legacy).lower()
    if "income" in legacy_str or "payroll" in legacy_str:
        return "Income"
    if "food" in legacy_str or "restaurant" in legacy_str or "coffee" in legacy_str:
        return "Dining" if "coffee" not in legacy_str else "Coffee"
    if "gas" in legacy_str or "fuel" in legacy_str:
        return "Gas"
    if "groceries" in legacy_str or "supermarket" in legacy_str:
        return "Groceries"
    if "subscription" in legacy_str or "streaming" in legacy_str:
        return "Subscriptions"
    if "travel" in legacy_str or "airline" in legacy_str or "hotel" in legacy_str:
        return "Travel"
    return "Other"


def guess_account_role(plaid_acct: dict) -> str:
    """Guess account role from Plaid subtype."""
    subtype = (plaid_acct.get("subtype") or "").lower()
    acct_type = (plaid_acct.get("type") or "").lower()
    if subtype in ("checking",):
        return "Spending"
    if subtype in ("savings", "money market", "cd"):
        return "Savings"
    if acct_type == "investment":
        return "Investment"
    return "Other"
