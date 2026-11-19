"""Input validation helpers shared by the services."""

import re
from datetime import date, datetime

from utils.errors import ApiError

ACCOUNT_TYPES = ("Savings", "Current", "Salary")
TRANSACTION_TYPES = ("credit", "debit")


def require_text(data, field, label, min_length=1, max_length=120):
    """Return a trimmed, required text value or raise a 422 ApiError."""
    value = (data.get(field) or "")
    value = value.strip() if isinstance(value, str) else value

    if not value:
        raise ApiError(f"{label} is required.", 422, {field: f"{label} is required."})
    if len(value) > max_length:
        raise ApiError(
            f"{label} must be {max_length} characters or fewer.",
            422,
            {field: f"{label} must be {max_length} characters or fewer."},
        )
    return value


def parse_date(raw, label, field):
    """Parse an ISO date (YYYY-MM-DD) or raise a 422 ApiError."""
    if not raw:
        raise ApiError(f"{label} is required.", 422, {field: f"{label} is required."})
    try:
        return datetime.strptime(str(raw).strip(), "%Y-%m-%d").date()
    except ValueError:
        raise ApiError(
            f"{label} must be a valid date (YYYY-MM-DD).",
            422,
            {field: f"{label} must be a valid date."},
        )


def parse_account_type(raw):
    value = (raw or "").strip()
    if value not in ACCOUNT_TYPES:
        raise ApiError(
            "Account type must be Savings, Current or Salary.",
            422,
            {"account_type": "Choose a valid account type."},
        )
    return value


def parse_transaction_type(raw):
    value = (raw or "").strip().lower()
    if value not in TRANSACTION_TYPES:
        raise ApiError(
            "Transaction type must be credit or debit.",
            422,
            {"transaction_type": "Choose Credit or Debit."},
        )
    return value


def mask_account_number(raw):
    """Store only a masked account number: XXXX + last four digits.

    Accepts '12345678', '1234 5678', 'XXXX1234' and keeps it stable on edit.
    """
    text = re.sub(r"[^0-9Xx]", "", str(raw or "").strip()).upper()
    if not text:
        raise ApiError("Account number is required.", 422, {"account_number": "Account number is required."})

    if text.startswith("XXXX") and len(text) == 8:
        last_four = text[4:]
    else:
        digits = re.sub(r"\D", "", text)
        if len(digits) < 4:
            raise ApiError(
                "Enter at least the last 4 digits of the account number.",
                422,
                {"account_number": "Enter at least 4 digits."},
            )
        last_four = digits[-4:]

    if not last_four.isdigit() or len(last_four) != 4:
        raise ApiError(
            "Enter at least the last 4 digits of the account number.",
            422,
            {"account_number": "Enter at least 4 digits."},
        )

    return f"XXXX{last_four}"


def parse_date_range(start_raw, end_raw):
    """Parse a statement period and check the order of the dates."""
    start = parse_date(start_raw, "Start date", "start_date")
    end = parse_date(end_raw, "End date", "end_date")
    if end < start:
        raise ApiError(
            "End date cannot be before the start date.",
            422,
            {"end_date": "End date must be on or after the start date."},
        )
    if start > date.today() and end > date.today():
        # Allowed (future dated transactions), but keep the API honest.
        pass
    return start, end
