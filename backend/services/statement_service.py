"""Balance calculation and statement building.

Rules implemented here:
  closing balance = opening balance + total credits - total debits
  credit: new balance = previous balance + amount
  debit:  new balance = previous balance - amount

For a selected period the opening balance is the account opening balance plus
every movement dated *before* the period start, and the closing balance is
derived from the transactions inside the period only.
"""

from datetime import date, datetime
from decimal import Decimal

from models import account as account_model
from models import transaction as transaction_model
from utils.errors import ApiError
from utils.money import money_str, to_decimal


def _movement(row):
    amount = to_decimal(row["amount"])
    return amount if row["transaction_type"] == "credit" else -amount


def build_statement(db, account_row, start_date, end_date):
    """Return a complete statement for one account and one date range."""
    rows = transaction_model.rows_for_account(db, account_row["account_id"])

    opening_balance = to_decimal(account_row["opening_balance"])
    period_rows = []

    for row in rows:
        transaction_date = date.fromisoformat(row["transaction_date"])
        if transaction_date < start_date:
            opening_balance += _movement(row)
        elif transaction_date <= end_date:
            period_rows.append(row)

    running_balance = opening_balance
    total_credits = Decimal("0.00")
    total_debits = Decimal("0.00")
    lines = []

    for row in period_rows:
        amount = to_decimal(row["amount"])
        is_credit = row["transaction_type"] == "credit"
        running_balance += amount if is_credit else -amount

        if is_credit:
            total_credits += amount
        else:
            total_debits += amount

        lines.append(
            {
                "transaction_id": row["transaction_id"],
                "reference": transaction_model.reference(row["transaction_id"]),
                "transaction_date": row["transaction_date"],
                "description": row["description"],
                "transaction_type": row["transaction_type"],
                "debit": "0.00" if is_credit else money_str(amount),
                "credit": money_str(amount) if is_credit else "0.00",
                "balance": money_str(running_balance),
            }
        )

    closing_balance = opening_balance + total_credits - total_debits

    return {
        "account": {
            "account_id": account_row["account_id"],
            "account_holder": account_row["account_holder"],
            "account_number_masked": account_row["account_number_masked"],
            "account_type": account_row["account_type"],
            "account_opening_balance": money_str(account_row["opening_balance"]),
            "created_at": account_row["created_at"],
        },
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
        "opening_balance": money_str(opening_balance),
        "closing_balance": money_str(closing_balance),
        "total_credits": money_str(total_credits),
        "total_debits": money_str(total_debits),
        "net_change": money_str(total_credits - total_debits),
        "transaction_count": len(lines),
        "transactions": lines,
        "generated_at": datetime.now().strftime("%d %b %Y, %I:%M %p"),
    }


def statement_for_account(db, user_id, account_id, start_date, end_date):
    account_row = account_model.get_row(db, account_id, user_id)
    if account_row is None:
        raise ApiError("Account not found.", 404)
    return build_statement(db, account_row, start_date, end_date)


def account_balance(db, account_row):
    """Current balance of an account using every transaction on record."""
    balance = to_decimal(account_row["opening_balance"])
    for row in transaction_model.rows_for_account(db, account_row["account_id"]):
        balance += _movement(row)
    return balance


def transaction_with_balances(db, user_id, transaction_id):
    """Details of one transaction including the balance before and after it."""
    transaction = transaction_model.get_for_user(db, transaction_id, user_id)
    if transaction is None:
        raise ApiError("Transaction not found.", 404)

    account_row = account_model.get_row(db, transaction["account_id"], user_id)
    running = to_decimal(account_row["opening_balance"])
    previous = None
    updated = None

    for row in transaction_model.rows_for_account(db, account_row["account_id"]):
        if row["transaction_id"] == transaction_id:
            previous = running
            updated = running + _movement(row)
            break
        running += _movement(row)

    if previous is None:  # Should not happen, but keeps the endpoint safe.
        previous = running
        updated = running

    return {
        **transaction,
        "account_opening_balance": money_str(account_row["opening_balance"]),
        "previous_balance": money_str(previous),
        "updated_balance": money_str(updated),
    }
