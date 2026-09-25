"""Tests for booking in-clinic consultations (issue DV-06).

Acceptance criteria covered: a consultation is booked for one specific
animal; times must land on the consulting timetable; double-bookings of a
slot/room are rejected with a clear message (two rooms available); a saved
consultation appears on that day's schedule and starts in a booked state;
cancelling keeps the record. The suite also covers both appointment kinds
(consultation and farm visit) as required by the delivery notes.
"""
from app.db import get_db

MONDAY = "2026-09-14"  # a clinic day (Mon/Wed/Fri 08:30-17:30)


def create_animal(client, name="Bella", species="dog"):
    """Seed one client and one animal directly (booking prerequisites)."""
    app = client.application
    with app.app_context():
        db = get_db()
        cursor = db.execute(
            "INSERT INTO client (name) VALUES (?)", (f"{name}'s owner",)
        )
        client_id = cursor.lastrowid
        cursor = db.execute(
            "INSERT INTO animals (client_id, name, species) VALUES (?, ?, ?)",
            (client_id, name, species),
        )
        db.commit()
        return cursor.lastrowid


def book(client, animal_id, scheduled_at, room):
    return client.post(
        "/api/consultations",
        json={"animal_id": animal_id, "scheduled_at": scheduled_at, "room": room},
    )


# --- Booking requires one specific animal ---------------------------------


def test_consultation_without_animal_is_rejected(client):
    response = book(client, None, f"{MONDAY}T09:00", 1)
    assert response.status_code == 400
    assert "animal" in response.get_json()["error"]


def test_consultation_with_unknown_animal_is_rejected(client):
    response = book(client, 999, f"{MONDAY}T09:00", 1)
    assert response.status_code == 404
    assert "animal" in response.get_json()["error"]


# --- Times must land on the consulting timetable --------------------------


def test_booking_outside_timetable_is_rejected(client):
    animal_id = create_animal(client)
    response = book(client, animal_id, f"{MONDAY}T17:30", 1)  # after last booking
    assert response.status_code == 400
    error = response.get_json()["error"]
    assert "fifteen-minute" in error
    assert "17:15" in error


def test_booking_on_closed_sunday_is_rejected(client):
    animal_id = create_animal(client)
    response = book(client, animal_id, "2026-09-20T09:00", 1)
    assert response.status_code == 400


def test_booking_off_the_fifteen_minute_grid_is_rejected(client):
    animal_id = create_animal(client)
    response = book(client, animal_id, f"{MONDAY}T09:10", 1)
    assert response.status_code == 400


def test_booking_with_invalid_datetime_is_rejected(client):
    animal_id = create_animal(client)
    response = book(client, animal_id, "not-a-datetime", 1)
    assert response.status_code == 400


# --- Double-bookings of a slot/room ---------------------------------------


def test_occupied_slot_room_rejected_with_clear_message(client):
    animal_id = create_animal(client)
    first = book(client, animal_id, f"{MONDAY}T09:00", 1)
    assert first.status_code == 201

    other_animal = create_animal(client, name="Rocky", species="cat")
    second = book(client, other_animal, f"{MONDAY}T09:00", 1)
    assert second.status_code == 409
    error = second.get_json()["error"]
    assert "Room 1" in error
    assert "09:00" in error


def test_same_slot_in_the_other_room_is_allowed(client):
    animal_id = create_animal(client)
    room_one = book(client, animal_id, f"{MONDAY}T09:00", 1)
    room_two = book(client, animal_id, f"{MONDAY}T09:00", 2)
    assert room_one.status_code == 201
    assert room_two.status_code == 201


def test_adjacent_slot_in_same_room_is_allowed(client):
    animal_id = create_animal(client)
    assert book(client, animal_id, f"{MONDAY}T09:00", 1).status_code == 201
    assert book(client, animal_id, f"{MONDAY}T09:15", 1).status_code == 201


def test_invalid_room_is_rejected(client):
    animal_id = create_animal(client)
    response = book(client, animal_id, f"{MONDAY}T09:00", 3)
    assert response.status_code == 400
    assert "room" in response.get_json()["error"]


# --- Day schedule and booked state ----------------------------------------


def test_saved_consultation_appears_on_day_schedule_as_booked(client):
    animal_id = create_animal(client)
    created = book(client, animal_id, f"{MONDAY}T09:00", 2)
    assert created.status_code == 201
    assert created.get_json()["consultation"]["status"] == "booked"

    schedule = client.get(f"/api/schedule?date={MONDAY}")
    assert schedule.status_code == 200
    consultations = schedule.get_json()["consultations"]
    assert len(consultations) == 1
    saved = consultations[0]
    assert saved["animal_id"] == animal_id
    assert saved["animal_name"] == "Bella"
    assert saved["room"] == 2
    assert saved["status"] == "booked"


def test_schedule_requires_a_date(client):
    response = client.get("/api/schedule")
    assert response.status_code == 400


def test_other_day_schedule_stays_empty(client):
    animal_id = create_animal(client)
    book(client, animal_id, f"{MONDAY}T09:00", 1)
    schedule = client.get("/api/schedule?date=2026-09-15").get_json()
    assert schedule["consultations"] == []
    assert schedule["farm_visits"] == []


# --- Cancelling keeps the record and frees the slot -----------------------


def test_cancelled_consultation_is_kept_and_slot_freed(client):
    animal_id = create_animal(client)
    created = book(client, animal_id, f"{MONDAY}T10:00", 1)
    consultation_id = created.get_json()["consultation"]["id"]

    cancelled = client.post(f"/api/consultations/{consultation_id}/cancel")
    assert cancelled.status_code == 200
    assert cancelled.get_json()["consultation"]["status"] == "cancelled"

    # The record is kept on the day's schedule.
    schedule = client.get(f"/api/schedule?date={MONDAY}").get_json()
    assert len(schedule["consultations"]) == 1
    assert schedule["consultations"][0]["status"] == "cancelled"

    # The slot can be booked again.
    animal_two = create_animal(client, name="Rocky", species="cat")
    rebooked = book(client, animal_two, f"{MONDAY}T10:00", 1)
    assert rebooked.status_code == 201


def test_cancelling_unknown_consultation_returns_404(client):
    response = client.post("/api/consultations/999/cancel")
    assert response.status_code == 404


# --- Both appointment kinds on the day's schedule -------------------------


def test_day_schedule_shows_consultation_and_farm_visit_kinds(client, app):
    """Delivery note: include a test of the two appointment kinds.

    A farm visit uses no consultation room, so it can overlap a
    consultation without blocking a room slot.
    """
    animal_id = create_animal(client)
    assert book(client, animal_id, f"{MONDAY}T09:00", 1).status_code == 201

    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO farm_visits (scheduled_at, duration_minutes, status)"
            " VALUES (?, 60, 'booked')",
            (f"{MONDAY}T09:00:00",),
        )
        db.commit()

    schedule = client.get(f"/api/schedule?date={MONDAY}").get_json()
    assert len(schedule["consultations"]) == 1
    assert schedule["consultations"][0]["room"] == 1
    assert len(schedule["farm_visits"]) == 1
    assert schedule["farm_visits"][0]["status"] == "booked"
