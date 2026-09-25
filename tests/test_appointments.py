"""Tests for rescheduling and cancelling appointments (issue DV-08).

Acceptance criteria covered: a consultation or farm visit can be moved to
another date/time under the same validation rules as booking; an appointment
can be cancelled and the cancelled record stays visible and distinguishable;
moving one appointment never affects any other appointment.
"""
from app.db import get_db

MONDAY = "2026-09-14"  # a clinic day (Mon/Wed/Fri 08:30-17:30)
TUESDAY = "2026-09-15"  # Tue/Thu mornings only for consultations
SUNDAY = "2026-09-20"  # closed


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


def seed_farm_visit(app, scheduled_at):
    """Insert one booked farm visit directly (booking itself is DV-07)."""
    with app.app_context():
        db = get_db()
        cursor = db.execute(
            "INSERT INTO farm_visits (scheduled_at, duration_minutes, status)"
            " VALUES (?, 60, 'booked')",
            (scheduled_at,),
        )
        db.commit()
        return int(cursor.lastrowid)


# --- Moving a consultation -------------------------------------------------


def test_reschedule_moves_consultation_to_new_time(client):
    animal_id = create_animal(client)
    consultation_id = book(client, animal_id, f"{MONDAY}T09:00", 1).get_json()[
        "consultation"
    ]["id"]

    moved = client.post(
        f"/api/consultations/{consultation_id}/reschedule",
        json={"scheduled_at": f"{MONDAY}T14:00"},
    )

    assert moved.status_code == 200
    saved = moved.get_json()["consultation"]
    assert saved["scheduled_at"] == f"{MONDAY}T14:00:00"
    assert saved["status"] == "booked"

    schedule = client.get(f"/api/schedule?date={MONDAY}").get_json()
    times = [c["scheduled_at"] for c in schedule["consultations"]]
    assert times == [f"{MONDAY}T14:00:00"]


def test_reschedule_rejects_time_outside_timetable(client):
    animal_id = create_animal(client)
    consultation_id = book(client, animal_id, f"{MONDAY}T09:00", 1).get_json()[
        "consultation"
    ]["id"]

    moved = client.post(
        f"/api/consultations/{consultation_id}/reschedule",
        json={"scheduled_at": f"{SUNDAY}T09:00"},
    )

    assert moved.status_code == 400
    assert "fifteen-minute" in moved.get_json()["error"]


def test_reschedule_rejects_invalid_datetime(client):
    animal_id = create_animal(client)
    consultation_id = book(client, animal_id, f"{MONDAY}T09:00", 1).get_json()[
        "consultation"
    ]["id"]

    moved = client.post(
        f"/api/consultations/{consultation_id}/reschedule",
        json={"scheduled_at": "not-a-datetime"},
    )

    assert moved.status_code == 400


def test_reschedule_rejects_clash_with_another_appointment(client):
    animal_id = create_animal(client)
    first = book(client, animal_id, f"{MONDAY}T09:00", 1).get_json()["consultation"]
    other_animal = create_animal(client, name="Rocky", species="cat")
    second = book(client, other_animal, f"{MONDAY}T10:00", 1).get_json()["consultation"]

    moved = client.post(
        f"/api/consultations/{second['id']}/reschedule",
        json={"scheduled_at": f"{MONDAY}T09:00"},
    )

    assert moved.status_code == 409
    assert "Room 1" in moved.get_json()["error"]
    # The clashing appointment kept its own booking untouched.
    still_there = client.get(f"/api/schedule?date={MONDAY}").get_json()
    assert still_there["consultations"][0]["id"] == first["id"]
    assert still_there["consultations"][0]["scheduled_at"] == f"{MONDAY}T09:00:00"


def test_reschedule_onto_own_current_slot_is_allowed(client):
    """Moving never clashes with the appointment's own current slot."""
    animal_id = create_animal(client)
    consultation_id = book(client, animal_id, f"{MONDAY}T09:00", 1).get_json()[
        "consultation"
    ]["id"]

    moved = client.post(
        f"/api/consultations/{consultation_id}/reschedule",
        json={"scheduled_at": f"{MONDAY}T09:00", "room": 1},
    )

    assert moved.status_code == 200


def test_reschedule_to_the_other_room_when_room_is_taken(client):
    animal_id = create_animal(client)
    consultation_id = book(client, animal_id, f"{MONDAY}T09:00", 1).get_json()[
        "consultation"
    ]["id"]
    other_animal = create_animal(client, name="Rocky", species="cat")
    book(client, other_animal, f"{MONDAY}T10:00", 1)

    moved = client.post(
        f"/api/consultations/{consultation_id}/reschedule",
        json={"scheduled_at": f"{MONDAY}T10:00", "room": 2},
    )

    assert moved.status_code == 200
    assert moved.get_json()["consultation"]["room"] == 2


def test_reschedule_rejects_unknown_room(client):
    animal_id = create_animal(client)
    consultation_id = book(client, animal_id, f"{MONDAY}T09:00", 1).get_json()[
        "consultation"
    ]["id"]

    moved = client.post(
        f"/api/consultations/{consultation_id}/reschedule",
        json={"scheduled_at": f"{MONDAY}T14:00", "room": 3},
    )

    assert moved.status_code == 400
    assert "room" in moved.get_json()["error"]


def test_reschedule_unknown_consultation_returns_404(client):
    response = client.post(
        "/api/consultations/999/reschedule",
        json={"scheduled_at": f"{MONDAY}T14:00"},
    )
    assert response.status_code == 404


def test_reschedule_cancelled_consultation_is_rejected(client):
    animal_id = create_animal(client)
    consultation_id = book(client, animal_id, f"{MONDAY}T09:00", 1).get_json()[
        "consultation"
    ]["id"]
    client.post(f"/api/consultations/{consultation_id}/cancel")

    moved = client.post(
        f"/api/consultations/{consultation_id}/reschedule",
        json={"scheduled_at": f"{MONDAY}T14:00"},
    )

    assert moved.status_code == 409
    assert "cancelled" in moved.get_json()["error"]


def test_rescheduling_one_appointment_leaves_others_untouched(client):
    animal_id = create_animal(client)
    first = book(client, animal_id, f"{MONDAY}T09:00", 1).get_json()["consultation"]
    other_animal = create_animal(client, name="Rocky", species="cat")
    second = book(client, other_animal, f"{MONDAY}T09:15", 1).get_json()["consultation"]

    moved = client.post(
        f"/api/consultations/{first['id']}/reschedule",
        json={"scheduled_at": f"{MONDAY}T14:00"},
    )
    assert moved.status_code == 200

    schedule = client.get(f"/api/schedule?date={MONDAY}").get_json()
    by_id = {c["id"]: c for c in schedule["consultations"]}
    assert by_id[second["id"]]["scheduled_at"] == f"{MONDAY}T09:15:00"
    assert by_id[second["id"]]["room"] == 1
    assert by_id[second["id"]]["status"] == "booked"
    assert by_id[first["id"]]["scheduled_at"] == f"{MONDAY}T14:00:00"


# --- Moving a farm visit ----------------------------------------------------


def test_reschedule_moves_farm_visit_to_another_day(client, app):
    farm_visit_id = seed_farm_visit(app, f"{MONDAY}T09:00:00")

    moved = client.post(
        f"/api/farm-visits/{farm_visit_id}/reschedule",
        json={"scheduled_at": f"{TUESDAY}T07:30"},
    )

    assert moved.status_code == 200
    saved = moved.get_json()["farm_visit"]
    assert saved["scheduled_at"] == f"{TUESDAY}T07:30:00"
    assert saved["status"] == "booked"

    old_day = client.get(f"/api/schedule?date={MONDAY}").get_json()
    assert old_day["farm_visits"] == []
    new_day = client.get(f"/api/schedule?date={TUESDAY}").get_json()
    assert [v["id"] for v in new_day["farm_visits"]] == [farm_visit_id]


def test_reschedule_farm_visit_unknown_returns_404(client):
    response = client.post(
        "/api/farm-visits/999/reschedule",
        json={"scheduled_at": f"{TUESDAY}T07:30"},
    )
    assert response.status_code == 404


def test_reschedule_farm_visit_rejects_invalid_datetime(client, app):
    farm_visit_id = seed_farm_visit(app, f"{MONDAY}T09:00:00")

    moved = client.post(
        f"/api/farm-visits/{farm_visit_id}/reschedule",
        json={"scheduled_at": "not-a-datetime"},
    )

    assert moved.status_code == 400


def test_reschedule_cancelled_farm_visit_is_rejected(client, app):
    farm_visit_id = seed_farm_visit(app, f"{MONDAY}T09:00:00")
    client.post(f"/api/farm-visits/{farm_visit_id}/cancel")

    moved = client.post(
        f"/api/farm-visits/{farm_visit_id}/reschedule",
        json={"scheduled_at": f"{TUESDAY}T07:30"},
    )

    assert moved.status_code == 409
    assert "cancelled" in moved.get_json()["error"]


# --- Cancelling a farm visit -------------------------------------------------


def test_cancelled_farm_visit_stays_visible_and_distinguishable(client, app):
    farm_visit_id = seed_farm_visit(app, f"{MONDAY}T09:00:00")

    cancelled = client.post(f"/api/farm-visits/{farm_visit_id}/cancel")

    assert cancelled.status_code == 200
    assert cancelled.get_json()["farm_visit"]["status"] == "cancelled"

    schedule = client.get(f"/api/schedule?date={MONDAY}").get_json()
    assert len(schedule["farm_visits"]) == 1
    assert schedule["farm_visits"][0]["status"] == "cancelled"


def test_cancel_unknown_farm_visit_returns_404(client):
    response = client.post("/api/farm-visits/999/cancel")
    assert response.status_code == 404
