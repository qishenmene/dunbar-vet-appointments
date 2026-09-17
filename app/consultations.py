"""In-clinic consultations: fifteen-minute slots in room 1 or room 2 (DV-06).

A consultation is booked for one specific animal, must land on the
consulting timetable (see app/timetable.py), starts in a ``booked`` state
and can be cancelled later — cancelled rows are kept for the records.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

from flask import Blueprint, jsonify, request

from .db import get_db
from .timetable import (
    CONSULTATION_ROOMS,
    SLOT_MINUTES,
    TIMETABLE_DESCRIPTION,
    is_valid_consultation_start,
)

bp = Blueprint("consultations", __name__, url_prefix="/api")


class BookingError(Exception):
    """Validation failure that maps onto an HTTP error response."""

    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.message = message
        self.status = status


def _parse_scheduled_at(raw) -> datetime:
    if not isinstance(raw, str) or not raw:
        raise BookingError(
            "scheduled_at is required as a local ISO datetime (YYYY-MM-DDTHH:MM)."
        )
    try:
        scheduled_at = datetime.fromisoformat(raw)
    except ValueError:
        raise BookingError(
            f"Invalid scheduled_at {raw!r}; use a local ISO datetime (YYYY-MM-DDTHH:MM)."
        )
    if scheduled_at.tzinfo is not None:
        raise BookingError("scheduled_at must be a local datetime without a timezone.")
    return scheduled_at


def _consultation_dict(row) -> dict:
    return {
        "id": row["id"],
        "animal_id": row["animal_id"],
        "animal_name": row["animal_name"],
        "room": row["room"],
        "scheduled_at": row["scheduled_at"],
        "duration_minutes": row["duration_minutes"],
        "status": row["status"],
    }


def get_consultation(consultation_id: int) -> dict | None:
    row = get_db().execute(
        "SELECT c.id, c.animal_id, a.name AS animal_name, c.room, c.scheduled_at,"
        " c.duration_minutes, c.status"
        " FROM consultations c JOIN animals a ON a.id = c.animal_id"
        " WHERE c.id = ?",
        (consultation_id,),
    ).fetchone()
    return _consultation_dict(row) if row is not None else None


def book_consultation(animal_id, scheduled_at_raw, room) -> dict:
    """Validate and save one consultation; returns its serialised record."""
    db = get_db()

    if animal_id is None:
        raise BookingError("A consultation must be booked for one specific animal.")
    if db.execute("SELECT 1 FROM animals WHERE id = ?", (animal_id,)).fetchone() is None:
        raise BookingError(
            f"No animal with id {animal_id}; a consultation must be booked"
            " for an existing animal.",
            404,
        )

    scheduled_at = _parse_scheduled_at(scheduled_at_raw)
    if not is_valid_consultation_start(scheduled_at):
        raise BookingError(
            "Consultations must land on the fifteen-minute consulting timetable:"
            f" {TIMETABLE_DESCRIPTION}."
        )

    if room is None:
        raise BookingError("A consultation room is required: room 1 or room 2.")
    if room not in CONSULTATION_ROOMS:
        raise BookingError(
            f"Unknown room {room}; consultations are held in room 1 or room 2."
        )

    day = scheduled_at.date().isoformat()
    slot_end = scheduled_at + timedelta(minutes=SLOT_MINUTES)
    clashes = db.execute(
        "SELECT scheduled_at, duration_minutes FROM consultations"
        " WHERE room = ? AND status != 'cancelled'"
        " AND substr(scheduled_at, 1, 10) = ?",
        (room, day),
    ).fetchall()
    for clash in clashes:
        existing_start = datetime.fromisoformat(clash["scheduled_at"])
        existing_end = existing_start + timedelta(minutes=clash["duration_minutes"])
        if existing_start < slot_end and existing_end > scheduled_at:
            raise BookingError(
                f"Room {room} is already booked from "
                f"{existing_start:%H:%M} to {existing_end:%H:%M} on {day};"
                " please pick a free slot or the other room.",
                409,
            )

    cursor = db.execute(
        "INSERT INTO consultations (animal_id, room, scheduled_at, duration_minutes, status)"
        " VALUES (?, ?, ?, ?, 'booked')",
        (animal_id, room, scheduled_at.isoformat(), SLOT_MINUTES),
    )
    db.commit()
    return get_consultation(cursor.lastrowid)


def cancel_consultation(consultation_id: int) -> dict:
    """Cancel a consultation, keeping the record on the books."""
    db = get_db()
    if db.execute(
        "SELECT 1 FROM consultations WHERE id = ?", (consultation_id,)
    ).fetchone() is None:
        raise BookingError(f"No consultation with id {consultation_id}.", 404)
    db.execute(
        "UPDATE consultations SET status = 'cancelled' WHERE id = ?",
        (consultation_id,),
    )
    db.commit()
    return get_consultation(consultation_id)


def day_schedule(schedule_date: date) -> dict:
    """The day's appointment book: consultations and farm visits."""
    db = get_db()
    day = schedule_date.isoformat()
    consultations = db.execute(
        "SELECT c.id, c.animal_id, a.name AS animal_name, c.room, c.scheduled_at,"
        " c.duration_minutes, c.status"
        " FROM consultations c JOIN animals a ON a.id = c.animal_id"
        " WHERE substr(c.scheduled_at, 1, 10) = ?"
        " ORDER BY c.scheduled_at, c.room",
        (day,),
    ).fetchall()
    farm_visits = db.execute(
        "SELECT id, scheduled_at, duration_minutes, status FROM farm_visits"
        " WHERE substr(scheduled_at, 1, 10) = ?"
        " ORDER BY scheduled_at",
        (day,),
    ).fetchall()
    return {
        "date": day,
        "consultations": [_consultation_dict(row) for row in consultations],
        "farm_visits": [dict(row) for row in farm_visits],
    }


@bp.post("/consultations")
def create_consultation():
    data = request.get_json(silent=True) or {}
    consultation = book_consultation(
        animal_id=data.get("animal_id"),
        scheduled_at_raw=data.get("scheduled_at"),
        room=data.get("room"),
    )
    return jsonify(consultation=consultation), 201


@bp.post("/consultations/<int:consultation_id>/cancel")
def cancel(consultation_id: int):
    return jsonify(consultation=cancel_consultation(consultation_id))


@bp.get("/schedule")
def get_day_schedule():
    raw = request.args.get("date")
    if not raw:
        raise BookingError("A date query parameter is required (format: YYYY-MM-DD).")
    try:
        schedule_date = date.fromisoformat(raw)
    except ValueError:
        raise BookingError(f"Invalid date {raw!r}; use format YYYY-MM-DD.")
    return jsonify(day_schedule(schedule_date))
