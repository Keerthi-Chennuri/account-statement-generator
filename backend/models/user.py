"""User model: queries and password helpers for the users table."""

import json

from werkzeug.security import check_password_hash, generate_password_hash

DEFAULT_PREFERENCES = {"default_statement_range": "30", "show_charts": True}


def parse_preferences(raw):
    """Turn the stored JSON text into a safe dictionary."""
    try:
        stored = json.loads(raw or "{}")
    except (TypeError, ValueError):
        stored = {}
    if not isinstance(stored, dict):
        stored = {}

    preferences = {**DEFAULT_PREFERENCES, **stored}
    preferences["show_charts"] = bool(preferences.get("show_charts", True))
    preferences["default_statement_range"] = str(preferences.get("default_statement_range", "30"))
    return preferences


def serialize_user(row):
    """Public user object (never includes the password hash)."""
    return {
        "user_id": row["user_id"],
        "name": row["name"],
        "username": row["username"],
        "role": row["role"],
        "preferences": parse_preferences(row["preferences"]),
        "created_at": row["created_at"],
    }


def get_by_id(db, user_id):
    return db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()


def get_by_username(db, username):
    return db.execute(
        "SELECT * FROM users WHERE LOWER(username) = ?", (username.lower(),)
    ).fetchone()


def verify_password(row, password):
    return check_password_hash(row["password_hash"], password)


def hash_password(password):
    return generate_password_hash(password)


def create_user(db, name, username, password, role="analyst"):
    cursor = db.execute(
        "INSERT INTO users (name, username, password_hash, role) VALUES (?, ?, ?, ?)",
        (name, username.lower(), hash_password(password), role),
    )
    db.commit()
    return cursor.lastrowid


def update_name(db, user_id, name):
    db.execute("UPDATE users SET name = ? WHERE user_id = ?", (name, user_id))
    db.commit()


def update_password(db, user_id, password):
    db.execute(
        "UPDATE users SET password_hash = ? WHERE user_id = ?",
        (hash_password(password), user_id),
    )
    db.commit()


def update_preferences(db, user_id, preferences):
    db.execute(
        "UPDATE users SET preferences = ? WHERE user_id = ?",
        (json.dumps(preferences), user_id),
    )
    db.commit()
