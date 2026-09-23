"""Application factory for the Dunbar Vet appointment system."""
from __future__ import annotations

from flask import Flask, jsonify, render_template

from config import INSTANCE_DIR, get_config

from .animals import animals_bp
from .appointments import bp as appointments_bp
from .consultations import BookingError, bp as consultations_bp
from .db import close_db, init_db_command
from .seed import seed_data_command


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__, instance_path=str(INSTANCE_DIR))

    config = get_config(config_name)
    app.config.from_object(config)
    app.config["DATABASE_FILE"] = str(config.database_file)
    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)

    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(seed_data_command)

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

    from .clients import clients_bp
    from .farm_runs import farm_runs_bp
    from .properties import properties_bp

    app.register_blueprint(clients_bp)
    app.register_blueprint(animals_bp)
    app.register_blueprint(properties_bp)
    app.register_blueprint(consultations_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(farm_runs_bp)

    return app
