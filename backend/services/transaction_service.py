"""Transaction management use cases."""

from models import account as account_model
from models import transaction as transaction_model
from utils.errors import ApiError
from utils.money import parse_amount
from utils.validators import parse_date, parse_transaction_type, require_text


def _validate(db, user_id, data):
    account_id = data.get("account_id")
    try:
        account_id = int(account_id)
    except (TypeError, ValueError):
        raise ApiError(
            "Select an account for this transaction.",
            422,
            {"account_id": "Select an account."},
        )

    if not account_model.exists(db, account_id, user_id):
        raise ApiError(
            "Transaction must belong to an existing account.",
            422,
            {"account_id": "Select one of your accounts."},
        )

    transaction_date = parse_date(data.get("transaction_date"), "Transaction date", "transaction_date")
    description = require_text(data, "description", "Description", max_length=160)
    transaction_type = parse_transaction_type(data.get("transaction_type"))

    try:
        amount = parse_amount(data.get("amount"))
    except ValueError as error:
        raise ApiError(str(error), 422, {"amount": str(error)})

    return account_id, transaction_date.isoformat(), description, transaction_type, amount


def list_transactions(db, user_id, filters):
    account_id = filters.get("account_id")
    if account_id:
        try:
            account_id = int(account_id)
        except (TypeError, ValueError):
            account_id = None

    transaction_type = (filters.get("type") or "").strip().lower()
    if transaction_type not in ("credit", "debit"):
        transaction_type = None

    return transaction_model.list_for_user(
        db,
        user_id,
        account_id=account_id,
        transaction_type=transaction_type,
        start_date=(filters.get("from") or "").strip() or None,
        end_date=(filters.get("to") or "").strip() or None,
        search=(filters.get("q") or "").strip(),
    )


def create_transaction(db, user_id, data):
    account_id, date, description, type_, amount = _validate(db, user_id, data)
    transaction_id = transaction_model.create(db, account_id, date, description, type_, amount)
    return get_transaction(db, user_id, transaction_id)


def update_transaction(db, user_id, transaction_id, data):
    if transaction_model.get_row(db, transaction_id, user_id) is None:
        raise ApiError("Transaction not found.", 404)

    account_id, date, description, type_, amount = _validate(db, user_id, data)
    transaction_model.update(db, transaction_id, date, description, type_, amount)
    return get_transaction(db, user_id, transaction_id)


def delete_transaction(db, user_id, transaction_id):
    if transaction_model.get_row(db, transaction_id, user_id) is None:
        raise ApiError("Transaction not found.", 404)
    transaction_model.delete(db, transaction_id)


def get_transaction(db, user_id, transaction_id):
    transaction = transaction_model.get_for_user(db, transaction_id, user_id)
    if transaction is None:
        raise ApiError("Transaction not found.", 404)
    return transaction
