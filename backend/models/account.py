"""Account model: every query is scoped to the signed-in user."""

from utils.money import money_str, to_decimal

BASE_SELECT = """
    SELECT a.account_id, a.user_id, a.account_holder, a.account_number_masked,
           a.account_type, a.opening_balance, a.created_at,
           COUNT(t.transaction_id) AS transaction_count,
           COALESCE(SUM(CASE WHEN t.transaction_type = 'credit' THEN t.amount
                             ELSE -t.amount END), 0) AS movement
    FROM accounts a
    LEFT JOIN transactions t ON t.account_id = a.account_id
    WHERE a.user_id = ?
"""

GROUP_BY = " GROUP BY a.account_id"


def serialize_account(row):
    opening = to_decimal(row["opening_balance"])
    current = opening + to_decimal(row["movement"])
    return {
        "account_id": row["account_id"],
        "account_holder": row["account_holder"],
        "account_number_masked": row["account_number_masked"],
        "account_type": row["account_type"],
        "opening_balance": money_str(opening),
        "current_balance": money_str(current),
        "transaction_count": int(row["transaction_count"] or 0),
        "created_at": row["created_at"],
    }


def list_for_user(db, user_id, search="", account_type=""):
    sql = BASE_SELECT
    params = [user_id]

    if account_type:
        sql += " AND a.account_type = ?"
        params.append(account_type)

    if search:
        sql += " AND (a.account_holder LIKE ? OR a.account_number_masked LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like])

    sql += GROUP_BY + " ORDER BY a.created_at DESC, a.account_id DESC"
    rows = db.execute(sql, params).fetchall()
    return [serialize_account(row) for row in rows]


def get_row(db, account_id, user_id):
    """Raw row (used for balance maths) or None when not owned by the user."""
    return db.execute(
        BASE_SELECT + " AND a.account_id = ?" + GROUP_BY,
        (user_id, account_id),
    ).fetchone()


def get_for_user(db, account_id, user_id):
    row = get_row(db, account_id, user_id)
    return serialize_account(row) if row else None


def exists(db, account_id, user_id):
    row = db.execute(
        "SELECT 1 FROM accounts WHERE account_id = ? AND user_id = ?",
        (account_id, user_id),
    ).fetchone()
    return row is not None


def create(db, user_id, account_holder, account_number_masked, account_type, opening_balance):
    cursor = db.execute(
        """INSERT INTO accounts
               (user_id, account_holder, account_number_masked, account_type, opening_balance)
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, account_holder, account_number_masked, account_type, f"{opening_balance:.2f}"),
    )
    db.commit()
    return cursor.lastrowid


def update(db, account_id, account_holder, account_number_masked, account_type, opening_balance):
    db.execute(
        """UPDATE accounts
              SET account_holder = ?, account_number_masked = ?, account_type = ?, opening_balance = ?
            WHERE account_id = ?""",
        (account_holder, account_number_masked, account_type, f"{opening_balance:.2f}", account_id),
    )
    db.commit()


def delete(db, account_id):
    db.execute("DELETE FROM accounts WHERE account_id = ?", (account_id,))
    db.commit()
