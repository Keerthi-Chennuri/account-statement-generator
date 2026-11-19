"""Dashboard aggregates: totals, recent activity and the monthly chart."""

import calendar
from datetime import date
from decimal import Decimal

from models import account as account_model
from models import transaction as transaction_model
from utils.money import money_str


def _monthly_series(transactions, months=6):
    today = date.today()
    buckets = []

    for offset in range(months - 1, -1, -1):
        index = today.year * 12 + (today.month - 1) - offset
        year, month_index = divmod(index, 12)
        month = month_index + 1
        buckets.append(
            {
                "key": f"{year}-{month:02d}",
                "label": f"{calendar.month_abbr[month]} {str(year)[2:]}",
                "credits": Decimal("0.00"),
                "debits": Decimal("0.00"),
            }
        )

    lookup = {bucket["key"]: bucket for bucket in buckets}

    for transaction in transactions:
        bucket = lookup.get(transaction["transaction_date"][:7])
        if bucket is None:
            continue
        amount = Decimal(transaction["amount"])
        if transaction["transaction_type"] == "credit":
            bucket["credits"] += amount
        else:
            bucket["debits"] += amount

    return [
        {
            "month": bucket["label"],
            "credits": money_str(bucket["credits"]),
            "debits": money_str(bucket["debits"]),
            "net": money_str(bucket["credits"] - bucket["debits"]),
        }
        for bucket in buckets
    ]


def build_summary(db, user_id):
    accounts = account_model.list_for_user(db, user_id)
    transactions = transaction_model.list_for_user(db, user_id)

    total_credits = Decimal("0.00")
    total_debits = Decimal("0.00")
    for transaction in transactions:
        amount = Decimal(transaction["amount"])
        if transaction["transaction_type"] == "credit":
            total_credits += amount
        else:
            total_debits += amount

    combined_balance = sum(
        (Decimal(account["current_balance"]) for account in accounts), Decimal("0.00")
    )

    return {
        "accounts_count": len(accounts),
        "transactions_count": len(transactions),
        "total_credits": money_str(total_credits),
        "total_debits": money_str(total_debits),
        "combined_balance": money_str(combined_balance),
        "recent_transactions": transactions[:6],
        "monthly": _monthly_series(transactions),
    }
