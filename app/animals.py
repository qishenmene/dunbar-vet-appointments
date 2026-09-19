"""Animal records attached to clients (DV-03).

Each animal is recorded individually against one existing client. The
minimum details are the animal's name and species, matching the practice
manager's phone workflow: callers give the animal's name first. Breed is
optional. Searching animals by name across all clients is delivered by
DV-04.
"""
from __future__ import annotations

import sqlite3

from flask import Blueprint, flash, redirect, render_template, request, url_for

from .clients import get_client, search_clients
from .db import get_db

animals_bp = Blueprint("animals", __name__, url_prefix="/animals")


@animals_bp.get("/")
def index():
    """List the animals of the selected client (``?client_id=``)."""
    db = get_db()
    client = _load_client(request.args.get("client_id", ""))
    animals = list_animals_for_client(db, client["id"]) if client else []
    return render_template(
        "animals/index.html",
        client=client,
        animals=animals,
        clients=search_clients(db),
    )


@animals_bp.post("/create")
def create():
    """Create an animal for an existing client; name and species are required."""
    client = _load_client(request.form.get("client_id", ""))
    name = request.form.get("name", "").strip()
    species = request.form.get("species", "").strip()
    breed = request.form.get("breed", "").strip()

    if client is None:
        flash("Select an existing client for the animal.")
        return redirect(url_for("animals.index"))
    if not name:
        flash("Animal name is required.")
    elif not species:
        flash("Species is required.")
    else:
        create_animal(get_db(), client["id"], name, species, breed)
        flash(f"Animal '{name}' ({species}) added for {client['name']}.")
    return redirect(url_for("animals.index", client_id=client["id"]))


def _load_client(raw_id: str) -> sqlite3.Row | None:
    """Return the client for a numeric id string, or None when invalid."""
    if not str(raw_id or "").strip().isdigit():
        return None
    return get_client(get_db(), int(str(raw_id).strip()))


def create_animal(
    db: sqlite3.Connection,
    client_id: int,
    name: str,
    species: str,
    breed: str = "",
) -> int:
    """Insert an animal attached to a client and return its id."""
    cursor = db.execute(
        "INSERT INTO animals (client_id, name, species, breed)"
        " VALUES (?, ?, ?, ?)",
        (client_id, name.strip(), species.strip(), breed.strip()),
    )
    db.commit()
    return int(cursor.lastrowid)


def get_animal(db: sqlite3.Connection, animal_id: int) -> sqlite3.Row | None:
    return db.execute(
        "SELECT a.*, c.name AS client_name, c.phone AS client_phone"
        " FROM animals a JOIN client c ON c.id = a.client_id"
        " WHERE a.id = ?",
        (animal_id,),
    ).fetchone()


def list_animals_for_client(
    db: sqlite3.Connection, client_id: int
) -> list[sqlite3.Row]:
    """Return every animal belonging to one client, ordered by name."""
    return list(
        db.execute(
            "SELECT a.*, c.name AS client_name FROM animals a"
            " JOIN client c ON c.id = a.client_id"
            " WHERE a.client_id = ?"
            " ORDER BY a.name COLLATE NOCASE",
            (client_id,),
        ).fetchall()
    )
