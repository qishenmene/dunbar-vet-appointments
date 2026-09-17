"""Tests for the consulting timetable module (issue DV-06).

The timetable is the agreed single source of truth: Mon/Wed/Fri
08:30-17:30 (last booking 17:15), Tue/Thu mornings until 10:15,
Sat 08:00-11:00, closed Sunday, all on a fifteen-minute grid.
"""
from datetime import datetime

from app.timetable import is_valid_consultation_start

# 2026 dates chosen so each weekday is unambiguous:
# 14 Mon, 15 Tue, 16 Wed, 17 Thu, 18 Fri, 19 Sat, 20 Sun.


def dt(text: str) -> datetime:
    return datetime.fromisoformat(text)


def test_monday_full_day_from_first_to_last_slot():
    assert is_valid_consultation_start(dt("2026-09-14T08:30"))
    assert is_valid_consultation_start(dt("2026-09-14T12:00"))
    assert is_valid_consultation_start(dt("2026-09-14T17:15"))  # last booking


def test_wednesday_and_friday_share_monday_hours():
    assert is_valid_consultation_start(dt("2026-09-16T08:30"))
    assert is_valid_consultation_start(dt("2026-09-16T17:15"))
    assert is_valid_consultation_start(dt("2026-09-18T12:00"))


def test_tuesday_and_thursday_mornings_only():
    assert is_valid_consultation_start(dt("2026-09-15T08:30"))
    assert is_valid_consultation_start(dt("2026-09-15T10:00"))  # last booking
    assert is_valid_consultation_start(dt("2026-09-17T09:45"))
    assert not is_valid_consultation_start(dt("2026-09-15T10:15"))
    assert not is_valid_consultation_start(dt("2026-09-17T12:00"))


def test_saturday_morning():
    assert is_valid_consultation_start(dt("2026-09-19T08:00"))
    assert is_valid_consultation_start(dt("2026-09-19T10:45"))  # last booking
    assert not is_valid_consultation_start(dt("2026-09-19T11:00"))


def test_sunday_closed():
    assert not is_valid_consultation_start(dt("2026-09-20T08:30"))
    assert not is_valid_consultation_start(dt("2026-09-20T10:00"))


def test_before_opening_and_after_last_booking_rejected():
    assert not is_valid_consultation_start(dt("2026-09-14T08:15"))
    assert not is_valid_consultation_start(dt("2026-09-14T17:30"))  # past 17:15


def test_off_grid_times_rejected():
    assert not is_valid_consultation_start(dt("2026-09-14T09:10"))
    assert not is_valid_consultation_start(dt("2026-09-14T08:30:30"))
    assert not is_valid_consultation_start(dt("2026-09-14T08:31"))
