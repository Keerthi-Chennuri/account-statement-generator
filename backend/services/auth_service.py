"""Authentication use cases: sign in, password change, profile and preferences."""

from models import user as user_model
from utils.errors import ApiError


def authenticate(db, username, password):
    row = user_model.get_by_username(db, (username or "").strip())
    if row is None or not user_model.verify_password(row, password or ""):
        raise ApiError("Invalid username or password.", 401)
    return user_model.serialize_user(row)


def change_password(db, user_id, current_password, new_password):
    row = user_model.get_by_id(db, user_id)
    fields = {}

    if not current_password:
        fields["current_password"] = "Current password is required."
    elif not user_model.verify_password(row, current_password):
        fields["current_password"] = "Current password is incorrect."

    if not new_password:
        fields["new_password"] = "New password is required."
    elif len(new_password) < 6:
        fields["new_password"] = "Use at least 6 characters."
    elif new_password == current_password:
        fields["new_password"] = "Choose a password different from the current one."

    if fields:
        raise ApiError("Please check the highlighted fields.", 422, fields)

    user_model.update_password(db, user_id, new_password)


def update_profile(db, user_id, name):
    name = (name or "").strip()
    if not name:
        raise ApiError("Name is required.", 422, {"name": "Name is required."})
    if len(name) > 80:
        raise ApiError("Name is too long.", 422, {"name": "Use 80 characters or fewer."})
    user_model.update_name(db, user_id, name)
    return user_model.serialize_user(user_model.get_by_id(db, user_id))


def update_preferences(db, user_id, preferences):
    current = user_model.parse_preferences(user_model.get_by_id(db, user_id)["preferences"])

    if "default_statement_range" in preferences:
        value = str(preferences["default_statement_range"])
        if value not in {"30", "90", "current_month"}:
            raise ApiError("Choose a valid statement range.", 422)
        current["default_statement_range"] = value

    if "show_charts" in preferences:
        current["show_charts"] = bool(preferences["show_charts"])

    user_model.update_preferences(db, user_id, current)
    return current
