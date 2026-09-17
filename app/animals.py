"""Minimal animal registry needed by the booking stories.

Consultations must be booked for one specific animal (issue DV-06), so this
module provides just enough to create animals. Full client and animal record
management is delivered by its own story and can extend this table.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from .db import get_db

bp = Blueprint("animals", __name__, url_prefix="/api")


@bp.post("/animals")
def create_animal():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    species = (data.get("species") or "").strip()
    if not name:
        return jsonify(error="An animal name is required."), 400
    if not species:
        return jsonify(error="An animal species is required."), 400
    db = get_db()
    cursor = db.execute(
        "INSERT INTO animals (name, species) VALUES (?, ?)",
        (name, species),
    )
    db.commit()
    animal = db.execute(
        "SELECT id, name, species FROM animals WHERE id = ?",
        (cursor.lastrowid,),
    ).fetchone()
    return jsonify(animal=dict(animal)), 201
