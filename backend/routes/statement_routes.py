"""Statement preview and PDF download endpoints."""

from flask import Blueprint, jsonify, request, send_file

from authentication.auth import current_user, login_required
from database.db import get_db
from pdf.statement_pdf import generate_statement_pdf
from services import statement_service
from utils.errors import ApiError
from utils.validators import parse_date_range

bp = Blueprint("statements", __name__, url_prefix="/api/statements")


def _requested_statement():
    account_id = request.args.get("account_id", type=int)
    if not account_id:
        raise ApiError(
            "Select an account to generate a statement.",
            422,
            {"account_id": "Select an account."},
        )

    start_date, end_date = parse_date_range(
        request.args.get("start_date"), request.args.get("end_date")
    )

    return statement_service.statement_for_account(
        get_db(), current_user()["user_id"], account_id, start_date, end_date
    )


@bp.get("/preview")
@login_required
def preview_statement():
    return jsonify({"statement": _requested_statement()})


@bp.get("/pdf")
@login_required
def download_statement():
    statement = _requested_statement()
    pdf_buffer = generate_statement_pdf(statement)

    period = statement["period"]
    masked = statement["account"]["account_number_masked"]
    filename = f"statement-{masked}-{period['start_date']}-to-{period['end_date']}.pdf"

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )
