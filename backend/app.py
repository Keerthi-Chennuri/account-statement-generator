"""Account Statement Generator - Flask API entry point.

Run locally with:
    python app.py
or:
    flask --app app run --debug
"""

import os

from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from config import Config
from database.db import init_db
from database.db import init_app as init_database
from database.seed import seed_demo_data
from routes.account_routes import bp as accounts_bp
from routes.auth_routes import bp as auth_bp
from routes.dashboard_routes import bp as dashboard_bp
from routes.statement_routes import bp as statements_bp
from routes.transaction_routes import bp as transactions_bp
from utils.errors import ApiError


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(os.path.dirname(app.config["DATABASE_PATH"]), exist_ok=True)

    CORS(
        app,
        origins=[
            app.config["FRONTEND_ORIGIN"],
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        ],
        supports_credentials=True,
        expose_headers=["Content-Disposition"],
    )

    init_database(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(accounts_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(statements_bp)
    app.register_blueprint(dashboard_bp)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "account-statement-generator"})

    @app.errorhandler(ApiError)
    def handle_api_error(error):
        payload = {"error": error.message}
        if error.fields:
            payload["fields"] = error.fields
        return jsonify(payload), error.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        return jsonify({"error": error.description or "Request failed."}), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        app.logger.exception("Unexpected server error")
        return jsonify({"error": "Unexpected server error. Please try again."}), 500

    @app.cli.command("seed-demo")
    def seed_demo_command():
        """Create the demo users, accounts and transactions."""
        if seed_demo_data():
            print("Demo data created.")
        else:
            print("Database already contains users - nothing was changed.")

    with app.app_context():
        init_db()
        seed_demo_data()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
