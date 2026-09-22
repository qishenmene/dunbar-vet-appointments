"""Reschedule or cancel an appointment (DV-08).

The practice manager can move a booked consultation or farm visit to another
date/time, or cancel it. Cancelled appointments stay on the books so the
appointment book keeps a record of what happened (the same rule DV-06 set
for consultation cancellations).

Validation rules for moving an appointment are the ones that applied at
booking time:

* A consultation must land on the fifteen-minute consulting timetable and
  into a free room slot — but a move never clashes with the appointment's
  own current slot, and moving never touches any other appointment.
* A farm visit is booked against a property with no consulting-room
  constraints, so only the datetime itself is validated.

Moving a cancelled appointment is rejected: a cancelled appointment is off
the books, so re-book a new appointment instead.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from .consultations import (
    CONSULTATION_ROOMS,
    BookingError,
    TIMETABLE_DESCRIPTION,
    _parse_scheduled_at,
    ensure_room_free,
    get_consultation,
)
from .db import get_db
from .timetable import is_valid_consultation_start

bp = Blueprint("appointments", __name__, url_prefix="/api")


# --- Consultation rescheduling ---------------------------------------------


def reschedule_consultation(consultation_id: int, scheduled_at_raw, room) -> dict:
    """Move one consultation to another date/time (and optionally room)."""
    db = get_db()
    current = db.execute(
        "SELECT id, room, status FROM consultations WHERE id = ?",
        (consultation_id,),
    ).fetchone()
    if current is None:
        raise BookingError(f"No consultation with id {consultation_id}.", 404)
    if current["status"] != "booked":
        raise BookingError(
            "A cancelled appointment cannot be rescheduled;"
            " book a new appointment instead.",
            409,
        )

    scheduled_at = _parse_scheduled_at(scheduled_at_raw)
    if not is_valid_consultation_start(scheduled_at):
        raise BookingError(
            "Consultations must land on the fifteen-minute consulting timetable:"
            f" {TIMETABLE_DESCRIPTION}."
        )

    # No room given means keep the consultation's current room.
    target_room = current["room"] if room is None else room
    if target_room not in CONSULTATION_ROOMS:
        raise BookingError(
            f"Unknown room {target_room}; consultations are held in room 1 or room 2."
        )
    ensure_room_free(db, target_room, scheduled_at, exclude_id=consultation_id)

    db.execute(
        "UPDATE consultations SET scheduled_at = ?, room = ? WHERE id = ?",
        (scheduled_at.isoformat(), target_room, consultation_id),
    )
    db.commit()
    return get_consultation(consultation_id)


@bp.post("/consultations/<int:consultation_id>/reschedule")
def reschedule(consultation_id: int):
    data = request.get_json(silent=True) or {}
    return jsonify(
        consultation=reschedule_consultation(
            consultation_id,
            data.get("scheduled_at"),
            data.get("room"),
        )
    )


# --- Farm visit rescheduling and cancelling ---------------------------------


def get_farm_visit(farm_visit_id: int) -> dict | None:
    row = get_db().execute(
        "SELECT id, property_id, scheduled_at, duration_minutes, status"
        " FROM farm_visits WHERE id = ?",
        (farm_visit_id,),
    ).fetchone()
    if row is None:
        return None
    return {
        "id": row["id"],
        "property_id": row["property_id"],
        "scheduled_at": row["scheduled_at"],
        "duration_minutes": row["duration_minutes"],
        "status": row["status"],
    }


def reschedule_farm_visit(farm_visit_id: int, scheduled_at_raw) -> dict:
    """Move one farm visit to another date/time."""
    db = get_db()
    current = db.execute(
        "SELECT id, status FROM farm_visits WHERE id = ?", (farm_visit_id,)
    ).fetchone()
    if current is None:
        raise BookingError(f"No farm visit with id {farm_visit_id}.", 404)
    if current["status"] != "booked":
        raise BookingError(
            "A cancelled appointment cannot be rescheduled;"
            " book a new appointment instead.",
            409,
        )

    scheduled_at = _parse_scheduled_at(scheduled_at_raw)
    db.execute(
        "UPDATE farm_visits SET scheduled_at = ? WHERE id = ?",
        (scheduled_at.isoformat(), farm_visit_id),
    )
    db.commit()
    return get_farm_visit(farm_visit_id)


def cancel_farm_visit(farm_visit_id: int) -> dict:
    """Cancel a farm visit, keeping the record on the books."""
    db = get_db()
    if db.execute(
        "SELECT 1 FROM farm_visits WHERE id = ?", (farm_visit_id,)
    ).fetchone() is None:
        raise BookingError(f"No farm visit with id {farm_visit_id}.", 404)
    db.execute(
        "UPDATE farm_visits SET status = 'cancelled' WHERE id = ?",
        (farm_visit_id,),
    )
    db.commit()
    return get_farm_visit(farm_visit_id)


@bp.post("/farm-visits/<int:farm_visit_id>/reschedule")
def reschedule_farm(farm_visit_id: int):
    data = request.get_json(silent=True) or {}
    return jsonify(farm_visit=reschedule_farm_visit(farm_visit_id, data.get("scheduled_at")))


@bp.post("/farm-visits/<int:farm_visit_id>/cancel")
def cancel_farm(farm_visit_id: int):
    return jsonify(farm_visit=cancel_farm_visit(farm_visit_id))
