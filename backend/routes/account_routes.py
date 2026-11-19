"""Account management endpoints."""

from flask import Blueprint, jsonify, request

from authentication.auth import current_user, login_required, roles_required
from database.db import get_db
from services import account_service

bp = Blueprint("accounts", __name__, url_prefix="/api/accounts")


def _user_id():
    return current_user()["user_id"]


@bp.get("")
@login_required
def list_accounts():
    accounts = account_service.list_accounts(
        get_db(),
        _user_id(),
        search=request.args.get("q", ""),
        account_type=request.args.get("type", ""),
    )
    return jsonify({"accounts": accounts})


@bp.get("/<int:account_id>")
@login_required
def get_account(account_id):
    return jsonify({"account": account_service.get_account(get_db(), _user_id(), account_id)})


@bp.post("")
@roles_required("admin")
def create_account():
    account = account_service.create_account(get_db(), _user_id(), request.get_json(silent=True) or {})
    return jsonify({"account": account, "message": "Account added successfully."}), 201


@bp.put("/<int:account_id>")
@roles_required("admin")
def update_account(account_id):
    account = account_service.update_account(
        get_db(), _user_id(), account_id, request.get_json(silent=True) or {}
    )
    return jsonify({"account": account, "message": "Account updated successfully."})


@bp.delete("/<int:account_id>")
@roles_required("admin")
def delete_account(account_id):
    account_service.delete_account(get_db(), _user_id(), account_id)
    return jsonify({"message": "Account and its transactions were deleted."})
