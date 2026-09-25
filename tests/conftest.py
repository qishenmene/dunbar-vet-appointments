"""Shared pytest fixtures."""
import os
import sys
from pathlib import Path

import pytest

# Make the project root importable when tests run from a clean checkout
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app  # noqa: E402
from app.db import close_db, get_db, init_db  # noqa: E402


@pytest.fixture()
def app(tmp_path, monkeypatch):
    db_path = tmp_path / "test.sqlite3"
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    application = create_app("testing")
    # Config class attributes are read from the environment at import time,
    # so point this test app's database at the per-test tmp_path explicitly.
    application.config["DATABASE_FILE"] = str(db_path)
    with application.app_context():
        init_db()
        yield application
        close_db()


@pytest.fixture()
def client(app):
    return app.test_client()
