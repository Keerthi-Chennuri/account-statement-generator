"""Transaction management endpoints."""

from flask import Blueprint, jsonify, request

from authentication.auth import current_user, login_required, roles_required
from database.db import get_db
from services import statement_service, transaction_service

bp = Blueprint("transactions", __name__, url_prefix="/api/transactions")


def _user_id():
    return current_user()["user_id"]


@bp.get("")
@login_required
def list_transactions():
    transactions = transaction_service.list_transactions(
        get_db(),
        _user_id(),
        {
            "account_id": request.args.get("account_id"),
            "type": request.args.get("type"),
            "from": request.args.get("from"),
            "to": request.args.get("to"),
            "q": request.args.get("q"),
        },
    )
    return jsonify({"transactions": transactions, "count": len(transactions)})


@bp.get("/<int:transaction_id>")
@login_required
def get_transaction(transaction_id):
    detail = statement_service.transaction_with_balances(get_db(), _user_id(), transaction_id)
    return jsonify({"transaction": detail})


@bp.post("")
@roles_required("admin")
def create_transaction():
    transaction = transaction_service.create_transaction(
        get_db(), _user_id(), request.get_json(silent=True) or {}
    )
    return jsonify({"transaction": transaction, "message": "Transaction recorded."}), 201


@bp.put("/<int:transaction_id>")
@roles_required("admin")
def update_transaction(transaction_id):
    transaction = transaction_service.update_transaction(
        get_db(), _user_id(), transaction_id, request.get_json(silent=True) or {}
    )
    return jsonify({"transaction": transaction, "message": "Transaction updated."})


@bp.delete("/<int:transaction_id>")
@roles_required("admin")
def delete_transaction(transaction_id):
    transaction_service.delete_transaction(get_db(), _user_id(), transaction_id)
    return jsonify({"message": "Transaction deleted."})
