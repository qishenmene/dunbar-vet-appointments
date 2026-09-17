"""Consulting timetable constants and validation.

Single source of truth for when in-clinic consultations may be booked,
agreed by the team before any booking views are built on top of it
(issue DV-06).

Sessions (fifteen-minute grid; every slot must fit inside the session):

* Monday / Wednesday / Friday: 08:30-17:30 (last booking 17:15)
* Tuesday / Thursday mornings: 08:30-10:15 (last booking 10:00)
* Saturday: 08:00-11:00 (last booking 10:45)
* Sunday: closed
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta

SLOT_MINUTES = 15

# Consultations are held in two rooms; a slot can be used once per room.
CONSULTATION_ROOMS = (1, 2)

# Weekday (0 = Monday) -> (session opens, session closes).
SESSIONS: dict[int, tuple[time, time]] = {
    0: (time(8, 30), time(17, 30)),  # Monday
    1: (time(8, 30), time(10, 15)),  # Tuesday (mornings only)
    2: (time(8, 30), time(17, 30)),  # Wednesday
    3: (time(8, 30), time(10, 15)),  # Thursday (mornings only)
    4: (time(8, 30), time(17, 30)),  # Friday
    5: (time(8, 0), time(11, 0)),  # Saturday
    # 6 = Sunday: closed.
}

TIMETABLE_DESCRIPTION = (
    "Mon/Wed/Fri 08:30-17:30 (last booking 17:15), "
    "Tue/Thu mornings until 10:15, Sat 08:00-11:00"
)


def session_for(day: date) -> tuple[time, time] | None:
    """Return (opens, closes) for the given day, or None when closed."""
    return SESSIONS.get(day.weekday())


def is_valid_consultation_start(when: datetime) -> bool:
    """True when *when* is a bookable consultation start time.

    The start must sit on the fifteen-minute grid (no seconds) and the whole
    slot must fit inside that day's session, so the last booking of a
    session starts one slot before closing time.
    """
    session = session_for(when.date())
    if session is None:
        return False
    if when.second or when.microsecond:
        return False
    if when.minute % SLOT_MINUTES != 0:
        return False
    opens, closes = session
    if when.time() < opens:
        return False
    slot_end = (when + timedelta(minutes=SLOT_MINUTES)).time()
    return slot_end <= closes
