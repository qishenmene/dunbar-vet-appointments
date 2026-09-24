"""Client record operations (DV-01).

Data-access functions for creating and searching clients. Search is a
case-insensitive substring match on the client name so reception can find a
caller while they wait on the phone.
"""
from __future__ import annotations

import sqlite3

from flask import Blueprint, flash, redirect, render_template, request, url_for

from .db import get_db

clients_bp = Blueprint("clients", __name__, url_prefix="/clients")


@clients_bp.get("/")
def index():
    """List active clients, optionally filtered by a name search."""
    term = request.args.get("q", "").strip()
    clients = search_clients(get_db(), term)
    return render_template("clients/index.html", clients=clients, q=term)


@clients_bp.post("/create")
def create():
    """Create a client. Name is required; phone and address are optional."""
    name = request.form.get("name", "").strip()
    if not name:
        flash("Client name is required.")
        return redirect(url_for("clients.index"))
    create_client(
        get_db(),
        name,
        request.form.get("phone", ""),
        request.form.get("address", ""),
    )
    flash(f"Client '{name}' added.")
    return redirect(url_for("clients.index"))


def create_client(db: sqlite3.Connection, name: str, phone: str = "", address: str = "") -> int:
    """Insert a new active client and return its id."""
    cur = db.execute(
        "INSERT INTO client (name, phone, address, is_active) VALUES (?, ?, ?, 1)",
        (name.strip(), phone.strip(), address.strip()),
    )
    db.commit()
    return int(cur.lastrowid)


def get_client(db: sqlite3.Connection, client_id: int) -> sqlite3.Row | None:
    return db.execute("SELECT * FROM client WHERE id = ?", (client_id,)).fetchone()


def search_clients(
    db: sqlite3.Connection, term: str = "", include_inactive: bool = False
) -> list[sqlite3.Row]:
    """Return clients whose name contains ``term`` (case-insensitive).

    By default only active clients are returned; inactive handling is used by
    later stories.
    """
    sql = "SELECT * FROM client WHERE name LIKE ? COLLATE NOCASE"
    params: list = [f"%{term.strip()}%"]
    if not include_inactive:
        sql += " AND is_active = 1"
    sql += " ORDER BY name COLLATE NOCASE"
    return list(db.execute(sql, params).fetchall())
