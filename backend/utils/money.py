"""Money helpers.

Amounts are handled with Decimal and always rounded to two decimal places,
so repeated additions never drift the way binary floating point can.
"""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

TWO_PLACES = Decimal("0.01")
MAX_AMOUNT = Decimal("999999999999.99")


def to_decimal(value) -> Decimal:
    """Convert a database value to an exact 2-decimal Decimal."""
    if value is None:
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    return Decimal(str(value)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def money_str(value) -> str:
    """Serialise money as a string such as '13000.00' (JSON-safe, no float)."""
    return f"{to_decimal(value):.2f}"


def parse_balance(raw, label="Opening balance"):
    """Validate an opening balance: zero is allowed, negatives are not."""
    if raw is None or str(raw).strip() == "":
        return Decimal("0.00")

    text = str(raw).strip().replace(",", "").replace("₹", "")
    try:
        amount = Decimal(text)
    except (InvalidOperation, ValueError):
        raise ValueError(f"{label} must be a valid number.")

    if not amount.is_finite():
        raise ValueError(f"{label} must be a valid number.")

    amount = amount.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    if amount < 0:
        raise ValueError(f"{label} cannot be negative.")
    if amount > MAX_AMOUNT:
        raise ValueError(f"{label} is too large.")
    return amount


def parse_amount(raw):
    """Validate a user supplied amount and return a Decimal.

    Raises ValueError with a friendly message when invalid.
    """
    if raw is None or str(raw).strip() == "":
        raise ValueError("Amount is required.")

    text = str(raw).strip().replace(",", "").replace("₹", "")
    try:
        amount = Decimal(text)
    except (InvalidOperation, ValueError):
        raise ValueError("Amount must be a valid number.")

    if not amount.is_finite():
        raise ValueError("Amount must be a valid number.")

    amount = amount.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")
    if amount > MAX_AMOUNT:
        raise ValueError("Amount is too large.")

    return amount
