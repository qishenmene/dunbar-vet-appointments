"""Seed sample data from the case study (DV-12).

Loads fictional clients, animals, properties, consultations and farm visits
so demos start from a realistic state. No real personal data is used; all
names and details are invented for the Dunbar Vet Clinic case study.
"""
from __future__ import annotations

import click
from flask import Flask

from .db import get_db, init_db


SEED_CLIENTS = [
    ("Martha Callaghan", "5550-0101", "14 Stony Creek Rd, Boonah QLD 4309"),
    ("Hugh McPherson", "5550-0102", "879 Cunningham St, Boonah QLD 4309"),
    ("Kalinga Downs Pastoral Co", "5550-0103", "Kalinga Downs, Kalbar QLD 4309"),
    ("Pru Trevena", "5550-0104", "3 George St, Aratula QLD 4309"),
]

SEED_ANIMALS = [
    # (animal_name, species) — client_id link arrives when DV-03 merges
    ("Bella", "dog"),
    ("Duke", "dog"),
    ("Pixie", "cat"),
    ("Rocky", "cat"),
    ("Barney", "dog"),
    ("Bossy", "cattle"),
    ("Daisy", "cattle"),
    ("Ginger", "cat"),
]

SEED_PROPERTIES = [
    # (client_name, property_name, locality, access_notes)
    ("Martha Callaghan", "Stony Creek House", "Stony Creek",
     "Three gates off the bitumen. Last gate has a chain — ring first, someone will open."),
    ("Kalinga Downs Pastoral Co", "Kalinga Downs", "Kalbar",
     "Bitumen to gravel, 6 km. Cattle grid at the boundary. Front gate code 4821."),
    ("Hugh McPherson", "McPherson Block", "Aratula",
     "Turn left after the creek crossing. Gate is always open, watch for dogs."),
]

SEED_CONSULTATIONS = [
    # (animal_name, room, scheduled_at)
    ("Bella", 1, "2026-09-28T09:00"),
    ("Pixie", 2, "2026-09-28T09:00"),
    ("Rocky", 1, "2026-09-28T09:15"),
    ("Barney", 1, "2026-09-28T10:00"),
    ("Duke", 2, "2026-09-30T14:00"),
    ("Ginger", 1, "2026-09-30T14:15"),
]

SEED_FARM_VISITS = [
    # (property_name, scheduled_at, duration_minutes, job_description, head_count, est_km)
    ("Stony Creek House", "2026-09-29T08:00", 60, "Pregnancy testing, 40 breeders", 40, 12),
    ("Kalinga Downs", "2026-09-29T10:00", 90, "TB test, whole herd", 120, 35),
    ("McPherson Block", "2026-09-29T13:30", 45, "Lame horse, left fore", 1, 8),
]


def _client_id_map(db) -> dict:
    rows = db.execute("SELECT id, name FROM client").fetchall()
    return {r["name"]: r["id"] for r in rows}


def _animal_id_map(db) -> dict:
    rows = db.execute("SELECT id, name FROM animals").fetchall()
    return {r["name"]: r["id"] for r in rows}


def _property_id_map(db) -> dict:
    rows = db.execute("SELECT id, name FROM property").fetchall()
    return {r["name"]: r["id"] for r in rows}


def seed_data(app: Flask):
    """Insert the case-study sample data into an initialised database."""
    with app.app_context():
        db = get_db()
        init_db()

        # Clear existing rows so re-seeding is idempotent (seed data is
        # fictional; real data should not coexist with the seed command).
        tables = {r["name"] for r in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        for t in ("farm_visits", "consultations", "property", "animals", "client"):
            if t in tables:
                db.execute(f"DELETE FROM {t}")

        # Clients
        for name, phone, address in SEED_CLIENTS:
            db.execute(
                "INSERT OR IGNORE INTO client (name, phone, address, is_active)"
                " VALUES (?, ?, ?, 1)",
                (name, phone, address),
            )

        # Animals (stub schema: name+species only; client_id link arrives with DV-03)
        for name, species in SEED_ANIMALS:
            db.execute(
                "INSERT OR IGNORE INTO animals (name, species) VALUES (?, ?)",
                (name, species),
            )

        # Properties
        c_map = _client_id_map(db)
        for owner, name, locality, notes in SEED_PROPERTIES:
            db.execute(
                "INSERT OR IGNORE INTO property (client_id, name, locality, access_notes)"
                " VALUES (?, ?, ?, ?)",
                (c_map[owner], name, locality, notes),
            )

        # Consultations (only if the table exists — DV-06 branch)
        tables = {r["name"] for r in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        if "consultations" in tables:
            a_map = _animal_id_map(db)
            for animal_name, room, scheduled_at in SEED_CONSULTATIONS:
                db.execute(
                    "INSERT INTO consultations (animal_id, room, scheduled_at,"
                    " duration_minutes, status)"
                    " VALUES (?, ?, ?, 15, 'booked')",
                    (a_map[animal_name], room, scheduled_at),
                )

        # Farm visits (only if the table exists — DV-07/DV-10 branch)
        if "farm_visits" in tables:
            p_map = _property_id_map(db)
            for prop_name, scheduled_at, dur, job, head, km in SEED_FARM_VISITS:
                db.execute(
                    "INSERT INTO farm_visits (property_id, scheduled_at,"
                    " duration_minutes, job_description, head_count, est_km, status)"
                    " VALUES (?, ?, ?, ?, ?, ?, 'booked')",
                    (p_map[prop_name], scheduled_at, dur, job, head, km),
                )

        db.commit()


@click.command("seed-db")
def seed_data_command():
    """Load fictional sample data from the case study (DV-12)."""
    from . import create_app
    app = create_app("production")
    seed_data(app)
    click.echo("Seed data loaded: 4 clients, 8 animals, 3 properties,"
               " 6 consultations, 3 farm visits.")
