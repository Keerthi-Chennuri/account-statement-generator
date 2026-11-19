"""Demo data for the prototype.

Two users are created:
  rahul / demo1234  (admin, can create, edit and delete)
  priya / demo1234  (analyst, read-only)

All names, account numbers and amounts are fictional.
"""

from datetime import date, timedelta

from models import user as user_model

TODAY = date.today()


def _day(days_ago):
    return (TODAY - timedelta(days=days_ago)).isoformat()


def _insert_account(db, user_id, holder, masked, account_type, opening_balance, days_ago):
    cursor = db.execute(
        """INSERT INTO accounts
               (user_id, account_holder, account_number_masked, account_type, opening_balance, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, holder, masked, account_type, opening_balance, f"{_day(days_ago)} 09:00:00"),
    )
    return cursor.lastrowid


def _insert_transaction(db, account_id, days_ago, description, transaction_type, amount):
    transaction_date = _day(days_ago)
    db.execute(
        """INSERT INTO transactions
               (account_id, transaction_date, description, transaction_type, amount, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (account_id, transaction_date, description, transaction_type, amount,
         f"{transaction_date} 10:00:00"),
    )


def seed_demo_data():
    """Insert the demo users, accounts and transactions when the DB is empty."""
    from database.db import get_db

    db = get_db()
    if db.execute("SELECT COUNT(*) AS total FROM users").fetchone()["total"] > 0:
        return False

    rahul_id = user_model.create_user(db, "Rahul Kumar", "rahul", "demo1234", "admin")
    priya_id = user_model.create_user(db, "Priya Sharma", "priya", "demo1234", "analyst")

    savings = _insert_account(db, rahul_id, "Rahul Kumar", "XXXX1234", "Savings", "10000.00", 210)
    current = _insert_account(db, rahul_id, "Rahul Kumar", "XXXX7788", "Current", "45000.00", 150)
    salary = _insert_account(db, rahul_id, "Rahul Kumar", "XXXX2190", "Salary", "25000.00", 120)
    priya_savings = _insert_account(db, priya_id, "Priya Sharma", "XXXX5501", "Savings", "18000.00", 90)

    # Savings account: the scenario from the brief (10,000 + 5,000 - 2,000) plus a
    # few months of realistic activity so the charts and statements look alive.
    for row in [
        (140, "Cash deposit at branch", "credit", "5000.00"),
        (138, "UPI payment - Stationery store", "debit", "2000.00"),
        (120, "Monthly salary credit", "credit", "65000.00"),
        (112, "House rent payment", "debit", "12000.00"),
        (96, "Groceries - BigBasket", "debit", "2450.50"),
        (84, "Freelance project payment", "credit", "15000.00"),
        (75, "Electricity bill - BESCOM", "debit", "3200.00"),
        (60, "Monthly salary credit", "credit", "65000.00"),
        (52, "Broadband subscription", "debit", "899.00"),
        (38, "UPI transfer to Priya Sharma", "debit", "1500.00"),
        (27, "Cash deposit", "credit", "5000.00"),
        (19, "ATM withdrawal", "debit", "2000.00"),
        (12, "Fuel - Indian Oil", "debit", "749.99"),
        (6, "Cashback reward", "credit", "1200.00"),
        (2, "UPI payment - Cafe Coffee Day", "debit", "480.00"),
    ]:
        _insert_transaction(db, savings, *row)

    for row in [
        (95, "Client invoice #A-2041 settled", "credit", "120000.00"),
        (88, "Vendor payout", "debit", "42000.00"),
        (64, "Client invoice #A-2052 settled", "credit", "85000.00"),
        (41, "Office supplies - Staples", "debit", "18500.00"),
        (23, "GST refund", "credit", "9600.00"),
        (9, "Software subscription", "debit", "2499.00"),
    ]:
        _insert_transaction(db, current, *row)

    for row in [
        (90, "Monthly salary credit", "credit", "65000.00"),
        (68, "Transfer to savings account", "debit", "20000.00"),
        (35, "Monthly salary credit", "credit", "65000.00"),
        (14, "Transfer to savings account", "debit", "15000.00"),
        (4, "Professional tax", "debit", "2500.00"),
    ]:
        _insert_transaction(db, salary, *row)

    for row in [
        (70, "Initial deposit", "credit", "18000.00"),
        (33, "Design workshop payment", "credit", "7000.00"),
        (11, "Book purchase", "debit", "1299.00"),
    ]:
        _insert_transaction(db, priya_savings, *row)

    db.commit()
    return True
