"""Application factory for the Dunbar Vet appointment system."""
from __future__ import annotations

from flask import Flask, jsonify, render_template

from config import INSTANCE_DIR, get_config

from .animals import bp as animals_bp
from .consultations import BookingError, bp as consultations_bp
from .db import close_db, init_db_command


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__, instance_path=str(INSTANCE_DIR))

    config = get_config(config_name)
    app.config.from_object(config)
    app.config["DATABASE_FILE"] = str(config.database_file)
    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)

    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.register_blueprint(animals_bp)
    app.register_blueprint(consultations_bp)

    @app.errorhandler(BookingError)
    def handle_booking_error(exc):
        return jsonify(error=exc.message), exc.status

    @app.get("/healthz")
    def healthz():
        """Liveness probe used by deployment scripts and CI."""
        return jsonify(status="ok", service="dunbar-vet-appointments")

    @app.get("/")
    def index():
        return render_template("index.html")

    from .animals import animals_bp
    from .clients import clients_bp
    from .properties import properties_bp

    app.register_blueprint(clients_bp)
    app.register_blueprint(animals_bp)
    app.register_blueprint(properties_bp)

    return app
