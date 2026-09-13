"""SQLite database helpers.

SQLite is used deliberately: the clinic needs the appointment book to keep
working when the internet is down, and a serverless file database has no
external service dependency. Domain tables are added by feature branches
delivering the sprint stories (see app/schema.sql).
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import click
from flask import Flask, current_app, g

SCHEMA_FILE = Path(__file__).resolve().parent / "schema.sql"


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE_FILE"],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(exc=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    db = get_db()
    db.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
    db.commit()


@click.command("init-db")
def init_db_command() -> None:
    """Create the database tables from app/schema.sql."""
    init_db()
    click.echo("Initialised the database.")


def init_app(app: Flask) -> None:
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
