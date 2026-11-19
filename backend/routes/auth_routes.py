"""Authentication, profile and settings endpoints."""

from flask import Blueprint, jsonify, request

from authentication.auth import current_user, login_required, login_user, logout_user
from database.db import get_db
from services import auth_service
from utils.errors import ApiError

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    fields = {}
    if not username:
        fields["username"] = "Username is required."
    if not password:
        fields["password"] = "Password is required."
    if fields:
        raise ApiError("Please fill in both fields.", 422, fields)

    user = auth_service.authenticate(get_db(), username, password)
    login_user(user["user_id"], remember=bool(data.get("remember")))
    return jsonify({"user": user})


@bp.post("/logout")
def logout():
    logout_user()
    return jsonify({"message": "You have been signed out."})


@bp.get("/me")
@login_required
def me():
    return jsonify({"user": current_user()})


@bp.put("/profile")
@login_required
def update_profile():
    data = request.get_json(silent=True) or {}
    user = auth_service.update_profile(get_db(), current_user()["user_id"], data.get("name"))
    return jsonify({"user": user, "message": "Profile updated."})


@bp.put("/preferences")
@login_required
def update_preferences():
    data = request.get_json(silent=True) or {}
    preferences = auth_service.update_preferences(get_db(), current_user()["user_id"], data)
    return jsonify({"preferences": preferences, "message": "Preferences saved."})


@bp.put("/password")
@login_required
def change_password():
    data = request.get_json(silent=True) or {}
    auth_service.change_password(
        get_db(),
        current_user()["user_id"],
        data.get("current_password") or "",
        data.get("new_password") or "",
    )
    return jsonify({"message": "Password updated successfully."})
