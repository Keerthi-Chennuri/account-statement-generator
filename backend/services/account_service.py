"""Account management use cases."""

from decimal import Decimal

from models import account as account_model
from utils.errors import ApiError
from utils.money import parse_balance
from utils.validators import mask_account_number, parse_account_type, require_text


def list_accounts(db, user_id, search="", account_type=""):
    account_type = (account_type or "").strip()
    if account_type and account_type not in ("Savings", "Current", "Salary"):
        account_type = ""
    return account_model.list_for_user(db, user_id, search=search.strip(), account_type=account_type)


def get_account(db, user_id, account_id):
    account = account_model.get_for_user(db, account_id, user_id)
    if account is None:
        raise ApiError("Account not found.", 404)
    return account


def create_account(db, user_id, data):
    account_holder = require_text(data, "account_holder", "Account holder name", max_length=80)
    masked = mask_account_number(data.get("account_number"))
    account_type = parse_account_type(data.get("account_type"))

    try:
        opening_balance = parse_balance(data.get("opening_balance"))
    except ValueError as error:
        raise ApiError(str(error), 422, {"opening_balance": str(error)})

    account_id = account_model.create(
        db, user_id, account_holder, masked, account_type, opening_balance
    )
    return account_model.get_for_user(db, account_id, user_id)


def update_account(db, user_id, account_id, data):
    if not account_model.exists(db, account_id, user_id):
        raise ApiError("Account not found.", 404)

    account_holder = require_text(data, "account_holder", "Account holder name", max_length=80)
    masked = mask_account_number(data.get("account_number"))
    account_type = parse_account_type(data.get("account_type"))

    try:
        opening_balance = parse_balance(data.get("opening_balance"))
    except ValueError as error:
        raise ApiError(str(error), 422, {"opening_balance": str(error)})

    account_model.update(db, account_id, account_holder, masked, account_type, opening_balance)
    return account_model.get_for_user(db, account_id, user_id)


def delete_account(db, user_id, account_id):
    if not account_model.exists(db, account_id, user_id):
        raise ApiError("Account not found.", 404)
    account_model.delete(db, account_id)


def total_opening_balance(accounts):
    return sum((Decimal(account["opening_balance"]) for account in accounts), Decimal("0.00"))
