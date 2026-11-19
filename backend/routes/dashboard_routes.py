"""Dashboard summary endpoint."""

from flask import Blueprint, jsonify

from authentication.auth import current_user, login_required
from database.db import get_db
from services import dashboard_service

bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@bp.get("/summary")
@login_required
def summary():
    return jsonify({"summary": dashboard_service.build_summary(get_db(), current_user()["user_id"])})
