"""Session based authentication.

The browser holds only a signed session cookie (HttpOnly). The user id lives
server-side in the cookie payload, so the client can never claim another
user's identity by sending an id.
"""

from functools import wraps

from flask import g, session

from database.db import get_db
from models.user import get_by_id, serialize_user
from utils.errors import ApiError


def login_user(user_id, remember=False):
    session.clear()
    session["user_id"] = user_id
    session.permanent = bool(remember)


def logout_user():
    session.clear()


def current_user():
    """Load the signed-in user once per request (or None)."""
    if "current_user" not in g:
        g.current_user = None
        user_id = session.get("user_id")
        if user_id:
            row = get_by_id(get_db(), user_id)
            if row is None:
                session.clear()
            else:
                g.current_user = serialize_user(row)
    return g.current_user


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            raise ApiError("Please sign in to continue.", 401)
        return view(*args, **kwargs)

    return wrapped


def roles_required(*allowed_roles):
    """Restrict a route to specific roles (admin can write, analyst is read-only)."""

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = current_user()
            if user is None:
                raise ApiError("Please sign in to continue.", 401)
            if user["role"] not in allowed_roles:
                raise ApiError(
                    "This demo account has read-only access. Sign in as an admin to make changes.",
                    403,
                )
            return view(*args, **kwargs)

        return wrapped

    return decorator
