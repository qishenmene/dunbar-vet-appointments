"""Rural property records with access notes (DV-05).

A client may own properties; each has a name, a locality and the gate/key/
road-access details the large-animal vet needs before arriving ("three
gates, the last one has a chain and no code — ring first"). Properties can
be created, found, updated and removed (case study, section 4). Farm visits
(DV-07) are booked against these records.
"""
from __future__ import annotations

import sqlite3

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from .clients import get_client, search_clients
from .db import get_db

properties_bp = Blueprint("properties", __name__, url_prefix="/properties")


@properties_bp.get("/")
def index():
    """List one client's properties (``?client_id=``) and edit one (``?edit=``)."""
    db = get_db()
    client = _load_client(request.args.get("client_id", ""))
    properties = list_properties_for_client(db, client["id"]) if client else []
    edit_property = None
    edit_raw = request.args.get("edit", "")
    if edit_raw.isdigit():
        edit_property = get_property(db, int(edit_raw))
        if edit_property is None:
            abort(404)
    return render_template(
        "properties/index.html",
        client=client,
        clients=search_clients(db),
        properties=properties,
        edit_property=edit_property,
    )


@properties_bp.get("/search")
def search():
    """Find properties by name across every client (DV-05)."""
    term = request.args.get("q", "").strip()
    properties = search_properties(get_db(), term) if term else []
    return render_template("properties/search.html", properties=properties, q=term)


@properties_bp.post("/create")
def create():
    client = _load_client(request.form.get("client_id", ""))
    name = request.form.get("name", "").strip()
    locality = request.form.get("locality", "").strip()
    access_notes = request.form.get("access_notes", "").strip()

    if client is None:
        flash("Select an existing client for the property.")
        return redirect(url_for("properties.index"))
    if not name:
        flash("Property name is required.")
    else:
        create_property(get_db(), client["id"], name, locality, access_notes)
        flash(f"Property '{name}' recorded for {client['name']}.")
    return redirect(url_for("properties.index", client_id=client["id"]))


@properties_bp.post("/<int:property_id>/update")
def update(property_id: int):
    db = get_db()
    property_record = get_property(db, property_id)
    if property_record is None:
        abort(404)
    name = request.form.get("name", "").strip()
    if not name:
        flash("Property name is required.")
        return redirect(
            url_for(
                "properties.index",
                client_id=property_record["client_id"],
                edit=property_id,
            )
        )
    update_property(
        db,
        property_id,
        name=name,
        locality=request.form.get("locality", "").strip(),
        access_notes=request.form.get("access_notes", "").strip(),
    )
    flash(f"Property '{name}' updated.")
    return redirect(
        url_for("properties.index", client_id=property_record["client_id"])
    )


@properties_bp.post("/<int:property_id>/delete")
def delete(property_id: int):
    db = get_db()
    property_record = get_property(db, property_id)
    if property_record is None:
        abort(404)
    delete_property(db, property_id)
    flash(f"Property '{property_record['name']}' removed.")
    return redirect(
        url_for("properties.index", client_id=property_record["client_id"])
    )


def _load_client(raw_id: str) -> sqlite3.Row | None:
    if not str(raw_id or "").strip().isdigit():
        return None
    return get_client(get_db(), int(str(raw_id).strip()))


def create_property(
    db: sqlite3.Connection,
    client_id: int,
    name: str,
    locality: str = "",
    access_notes: str = "",
) -> int:
    cursor = db.execute(
        "INSERT INTO property (client_id, name, locality, access_notes)"
        " VALUES (?, ?, ?, ?)",
        (client_id, name.strip(), locality.strip(), access_notes.strip()),
    )
    db.commit()
    return int(cursor.lastrowid)


def get_property(db: sqlite3.Connection, property_id: int) -> sqlite3.Row | None:
    return db.execute(
        "SELECT p.*, c.name AS client_name, c.phone AS client_phone"
        " FROM property p JOIN client c ON c.id = p.client_id"
        " WHERE p.id = ?",
        (property_id,),
    ).fetchone()


def list_properties_for_client(
    db: sqlite3.Connection, client_id: int
) -> list[sqlite3.Row]:
    return list(
        db.execute(
            "SELECT * FROM property WHERE client_id = ?"
            " ORDER BY name COLLATE NOCASE",
            (client_id,),
        ).fetchall()
    )


def search_properties(db: sqlite3.Connection, term: str) -> list[sqlite3.Row]:
    """Return properties whose name contains ``term``, across all clients."""
    return list(
        db.execute(
            "SELECT p.*, c.name AS client_name, c.phone AS client_phone"
            " FROM property p JOIN client c ON c.id = p.client_id"
            " WHERE c.is_active = 1 AND p.name LIKE ? COLLATE NOCASE"
            " ORDER BY p.name COLLATE NOCASE, c.name COLLATE NOCASE",
            (f"%{term.strip()}%",),
        ).fetchall()
    )


def update_property(db: sqlite3.Connection, property_id: int, **fields) -> None:
    allowed = ("name", "locality", "access_notes")
    assignments = [f"{key} = ?" for key in fields if key in allowed]
    values = [fields[key] for key in fields if key in allowed]
    if not assignments:
        return
    values.append(property_id)
    db.execute(
        f"UPDATE property SET {', '.join(assignments)} WHERE id = ?", values
    )
    db.commit()


def delete_property(db: sqlite3.Connection, property_id: int) -> None:
    db.execute("DELETE FROM property WHERE id = ?", (property_id,))
    db.commit()
