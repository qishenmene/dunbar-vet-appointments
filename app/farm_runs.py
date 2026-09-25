"""Farm day run sheet (DV-10).

A read-only, time-ordered view of one day's farm visits for the large-animal
vet, modelled on the green diary run sheet (case study, Document B). Each row
shows the start time, property, locality, client/contact, job, head count,
estimated duration/km and the property's gate/key/ring-first access notes.

Scope boundaries (agreed assumptions for this story):

* Booking and cancelling farm visits is DV-07/DV-08; this module only reads.
* No route optimisation between properties: visits are shown in their
  scheduled working order, matching today's manual green diary.
* The view inner-joins ``property`` and ``client``: a farm visit without a
  linked property cannot be driven to and so never appears on the run sheet
  (the nullable ``farm_visits.property_id`` exists only to keep the DV-06
  stub rows working until DV-07 enforces a mandatory property at booking).
"""
from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta

from flask import Blueprint, abort, render_template, request

from .db import get_db

farm_runs_bp = Blueprint("farm_runs", __name__, url_prefix="/farm")


def create_farm_visit(
    db: sqlite3.Connection,
    property_id: int,
    scheduled_at: str,
    duration_minutes: int = 60,
    job_description: str = "",
    head_count: int | None = None,
    est_km: int | None = None,
) -> int:
    """Insert a farm visit row and return its id.

    Booking validation (timetable, double booking, mandatory fields beyond
    the property link) belongs to DV-07; this helper supports tests and seed
    data and the run-sheet story.
    """
    cur = db.execute(
        """
        INSERT INTO farm_visits (property_id, scheduled_at, duration_minutes,
                                 job_description, head_count, est_km)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            property_id,
            scheduled_at,
            duration_minutes,
            job_description,
            head_count,
            est_km,
        ),
    )
    db.commit()
    return int(cur.lastrowid)


def list_farm_run(db: sqlite3.Connection, day: date) -> list[sqlite3.Row]:
    """Return one day's farm visits in scheduled order, both kinds of row.

    Cancelled visits are kept and flagged in the template so the run sheet
    retains a record of cancelled work, as the manual book does.
    """
    return db.execute(
        """
        SELECT fv.id,
               fv.scheduled_at,
               fv.duration_minutes,
               fv.status,
               fv.job_description,
               fv.head_count,
               fv.est_km,
               p.name        AS property_name,
               p.locality    AS locality,
               p.access_notes AS access_notes,
               c.name        AS client_name,
               c.phone       AS client_phone
          FROM farm_visits fv
          JOIN property p ON p.id = fv.property_id
          JOIN client   c ON c.id = p.client_id
         WHERE substr(fv.scheduled_at, 1, 10) = ?
         ORDER BY fv.scheduled_at
        """,
        (day.isoformat(),),
    ).fetchall()


def _parse_day(raw: str | None) -> date:
    if raw:
        try:
            return date.fromisoformat(raw)
        except ValueError as exc:
            abort(400, description="Date must use the format YYYY-MM-DD.")
    return date.today()


@farm_runs_bp.get("/run")
def run_sheet():
    """HTML run sheet for ?date=YYYY-MM-DD (defaults to today)."""
    day = _parse_day(request.args.get("date"))
    visits = list_farm_run(get_db(), day)
    return render_template(
        "farm_runs/day.html",
        day=day,
        weekday=day.strftime("%A"),
        visits=visits,
        previous_day=(day - timedelta(days=1)).isoformat(),
        next_day=(day + timedelta(days=1)).isoformat(),
    )
