"""Application configuration.

Values can be overridden with environment variables, so the same code runs
locally (SQLite) and in a hosted environment.
"""

import os
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    # Used by Flask to sign the session cookie. Set a real secret in production.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-secret-change-me")

    # SQLite file for development. Swap this out for a MySQL connection later.
    DATABASE_PATH = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "database", "statement.db"))

    # Where the React development server runs (used by CORS).
    FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173")

    # Secure cookie settings
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # Reject very large request bodies
    MAX_CONTENT_LENGTH = 1024 * 1024

    JSON_SORT_KEYS = False
