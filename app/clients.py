"""Client record operations (DV-01, DV-02).

Data-access functions for creating, searching, updating and activating or
deactivating clients. Search is a case-insensitive substring match on the
client name so reception can find a caller while they wait on the phone.

Clients are never deleted: a client who has left the district is marked
inactive, so their appointment history stays intact (DV-02).
"""
from __future__ import annotations

import sqlite3

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from .db import get_db

clients_bp = Blueprint("clients", __name__, url_prefix="/clients")


@clients_bp.get("/")
def index():
    """List clients, optionally filtered by a name search.

    Active clients are shown by default. Passing ``all=1`` also includes
    inactive clients so a retired client can still be found and reactivated.
    """
    term = request.args.get("q", "").strip()
    include_inactive = request.args.get("all") == "1"
    clients = search_clients(get_db(), term, include_inactive=include_inactive)
    return render_template(
        "clients/index.html",
        clients=clients,
        q=term,
        include_inactive=include_inactive,
    )


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


@clients_bp.get("/<int:client_id>/edit")
def edit(client_id: int):
    """Show the edit form for one client."""
    client = get_client(get_db(), client_id)
    if client is None:
        abort(404)
    return render_template("clients/edit.html", client=client)


@clients_bp.post("/<int:client_id>/update")
def update(client_id: int):
    """Update a client's name, phone and address. Only that row is touched."""
    db = get_db()
    client = get_client(db, client_id)
    if client is None:
        abort(404)
    name = request.form.get("name", "").strip()
    if not name:
        flash("Client name is required.")
        return redirect(url_for("clients.edit", client_id=client_id))
    update_client(
        db,
        client_id,
        name,
        request.form.get("phone", ""),
        request.form.get("address", ""),
    )
    flash(f"Client '{name}' updated.")
    return redirect(url_for("clients.index"))


@clients_bp.post("/<int:client_id>/deactivate")
def deactivate(client_id: int):
    """Mark a client inactive; the record and its history are kept."""
    db = get_db()
    client = get_client(db, client_id)
    if client is None:
        abort(404)
    set_client_active(db, client_id, False)
    flash(f"Client '{client['name']}' marked inactive.")
    return redirect(url_for("clients.index"))


@clients_bp.post("/<int:client_id>/activate")
def activate(client_id: int):
    """Reactivate an inactive client."""
    db = get_db()
    client = get_client(db, client_id)
    if client is None:
        abort(404)
    set_client_active(db, client_id, True)
    flash(f"Client '{client['name']}' reactivated.")
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


def update_client(
    db: sqlite3.Connection, client_id: int, name: str, phone: str = "", address: str = ""
) -> None:
    """Update one client's details; rows for other clients are untouched."""
    db.execute(
        "UPDATE client SET name = ?, phone = ?, address = ? WHERE id = ?",
        (name.strip(), phone.strip(), address.strip(), client_id),
    )
    db.commit()


def set_client_active(db: sqlite3.Connection, client_id: int, active: bool) -> None:
    """Set the active flag of one client without deleting the record."""
    db.execute(
        "UPDATE client SET is_active = ? WHERE id = ?",
        (1 if active else 0, client_id),
    )
    db.commit()


def search_clients(
    db: sqlite3.Connection, term: str = "", include_inactive: bool = False
) -> list[sqlite3.Row]:
    """Return clients whose name contains ``term`` (case-insensitive).

    By default only active clients are returned; inactive clients are included
    when ``include_inactive`` is set so retired clients remain findable.
    """
    sql = "SELECT * FROM client WHERE name LIKE ? COLLATE NOCASE"
    params: list = [f"%{term.strip()}%"]
    if not include_inactive:
        sql += " AND is_active = 1"
    sql += " ORDER BY name COLLATE NOCASE"
    return list(db.execute(sql, params).fetchall())
