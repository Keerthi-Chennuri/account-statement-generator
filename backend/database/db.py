"""SQLite connection helpers.

One connection is created per request and stored on Flask's ``g`` object.
"""

import sqlite3

from flask import current_app, g


def get_db():
    """Open (or reuse) the database connection for this request."""
    if "db" not in g:
        connection = sqlite3.connect(current_app.config["DATABASE_PATH"])
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        g.db = connection
    return g.db


def close_db(exception=None):
    """Close the request connection when the request finishes."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create tables and indexes if they do not exist yet."""
    db = get_db()
    schema = current_app.open_resource("database/schema.sql").read().decode("utf-8")
    db.executescript(schema)
    db.commit()


def init_app(app):
    app.teardown_appcontext(close_db)
