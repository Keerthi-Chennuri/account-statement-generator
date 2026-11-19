"""Transaction model: filters, CRUD and the joined account information."""

from datetime import date

from utils.money import money_str

BASE_SELECT = """
    SELECT t.transaction_id, t.account_id, t.transaction_date, t.description,
           t.transaction_type, t.amount, t.created_at,
           a.account_holder, a.account_number_masked, a.account_type
    FROM transactions t
    JOIN accounts a ON a.account_id = t.account_id
    WHERE a.user_id = ?
"""


def reference(transaction_id):
    """Human friendly id used in the UI, statements and the PDF."""
    return f"TXN{int(transaction_id):06d}"


def serialize_transaction(row):
    transaction_date = row["transaction_date"]
    is_future = transaction_date > date.today().isoformat()
    return {
        "transaction_id": row["transaction_id"],
        "reference": reference(row["transaction_id"]),
        "account_id": row["account_id"],
        "account_holder": row["account_holder"],
        "account_number_masked": row["account_number_masked"],
        "account_type": row["account_type"],
        "transaction_date": transaction_date,
        "description": row["description"],
        "transaction_type": row["transaction_type"],
        "amount": money_str(row["amount"]),
        "status": "Pending" if is_future else "Completed",
        "created_at": row["created_at"],
    }


def list_for_user(db, user_id, account_id=None, transaction_type=None,
                  start_date=None, end_date=None, search=""):
    sql = BASE_SELECT
    params = [user_id]

    if account_id:
        sql += " AND t.account_id = ?"
        params.append(account_id)

    if transaction_type:
        sql += " AND t.transaction_type = ?"
        params.append(transaction_type)

    if start_date:
        sql += " AND t.transaction_date >= ?"
        params.append(start_date)

    if end_date:
        sql += " AND t.transaction_date <= ?"
        params.append(end_date)

    if search:
        like = f"%{search}%"
        sql += """ AND (t.description LIKE ? OR a.account_holder LIKE ?
                        OR a.account_number_masked LIKE ? OR CAST(t.transaction_id AS TEXT) LIKE ?)"""
        params.extend([like, like, like, like])

    sql += " ORDER BY t.transaction_date DESC, t.transaction_id DESC"
    rows = db.execute(sql, params).fetchall()
    return [serialize_transaction(row) for row in rows]


def get_row(db, transaction_id, user_id):
    return db.execute(
        BASE_SELECT + " AND t.transaction_id = ?", (user_id, transaction_id)
    ).fetchone()


def get_for_user(db, transaction_id, user_id):
    row = get_row(db, transaction_id, user_id)
    return serialize_transaction(row) if row else None


def rows_for_account(db, account_id):
    """All transactions of one account in chronological order."""
    return db.execute(
        """SELECT * FROM transactions
            WHERE account_id = ?
            ORDER BY transaction_date ASC, created_at ASC, transaction_id ASC""",
        (account_id,),
    ).fetchall()


def create(db, account_id, transaction_date, description, transaction_type, amount):
    cursor = db.execute(
        """INSERT INTO transactions
               (account_id, transaction_date, description, transaction_type, amount)
           VALUES (?, ?, ?, ?, ?)""",
        (account_id, transaction_date, description, transaction_type, f"{amount:.2f}"),
    )
    db.commit()
    return cursor.lastrowid


def update(db, transaction_id, transaction_date, description, transaction_type, amount):
    db.execute(
        """UPDATE transactions
              SET transaction_date = ?, description = ?, transaction_type = ?, amount = ?
            WHERE transaction_id = ?""",
        (transaction_date, description, transaction_type, f"{amount:.2f}", transaction_id),
    )
    db.commit()


def delete(db, transaction_id):
    db.execute("DELETE FROM transactions WHERE transaction_id = ?", (transaction_id,))
    db.commit()
