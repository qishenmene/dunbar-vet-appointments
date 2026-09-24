"""Tests for DV-10: the farm day run sheet.

The run sheet is a read-only time-ordered view of one day's farm visits with
property, client and access details. Booking farm visits is DV-07; these
tests use a small data helper to seed rows directly.
"""

from app.clients import create_client
from app.db import get_db
from app.farm_runs import create_farm_visit
from app.properties import create_property

MONDAY = "2026-09-14"  # a Monday, a normal farm-run day


def _property(app, name="Kalinga Downs", locality="Coulson",
              client_name="R & M Petrie", phone="0427 118 553",
              access_notes="gate code 4417"):
    with app.app_context():
        client_id = create_client(get_db(), client_name, phone)
        property_id = create_property(
            get_db(), client_id, name, locality, access_notes
        )
    return property_id


def _visit(app, property_id, when, duration=60, job="", head=None, km=None,
           status="booked"):
    with app.app_context():
        visit_id = create_farm_visit(
            get_db(), property_id, f"{MONDAY}T{when}:00", duration, job,
            head, km,
        )
        if status == "cancelled":
            db = get_db()
            db.execute(
                "UPDATE farm_visits SET status = 'cancelled' WHERE id = ?",
                (visit_id,),
            )
            db.commit()
    return visit_id


def test_empty_day_shows_message(client):
    resp = client.get("/farm/run?date=2026-09-15")
    assert resp.status_code == 200
    assert b"No farm visits booked for this day." in resp.data
    assert b"Tuesday 15 September 2026" in resp.data


def test_run_sheet_defaults_to_today(client):
    resp = client.get("/farm/run")
    assert resp.status_code == 200


def test_invalid_date_returns_400(client):
    resp = client.get("/farm/run?date=14-09-2026")
    assert resp.status_code == 400


def test_visits_listed_in_scheduled_order(client, app):
    first = _property(app, "Kalinga Downs", client_name="R & M Petrie")
    second = _property(app, "Willow Bend", "Milford", "Carmel Sanderson")
    third = _property(app, "Stony Creek", "Bunjurgen", "Bridie Callaghan")
    # Inserted deliberately out of order; the sheet must re-order by time.
    _visit(app, third, "16:00", job="Boar cut")
    _visit(app, first, "11:15", job="Preg test")
    _visit(app, second, "14:45", job="Calving check")

    page = client.get(f"/farm/run?date={MONDAY}").data

    assert page.index(b"Kalinga Downs") < page.index(b"Willow Bend")
    assert page.index(b"Willow Bend") < page.index(b"Stony Creek")
    assert page.index(b"11:15") < page.index(b"14:45") < page.index(b"16:00")


def test_row_shows_property_client_access_and_estimate(client, app):
    property_id = _property(app)
    _visit(app, property_id, "11:15", duration=180,
           job="Preg test", head=120, km=60)

    page = client.get(f"/farm/run?date={MONDAY}").data

    assert b"Kalinga Downs" in page
    assert b"Coulson" in page
    assert b"R &amp; M Petrie" in page
    assert b"0427 118 553" in page
    assert b"Preg test" in page
    assert b">120<" in page
    assert b">60<" in page
    assert b"3 hr" in page
    assert b"gate code 4417" in page


def test_cancelled_visit_remains_visible_and_marked(client, app):
    property_id = _property(app, name="Willow Bend", locality="Milford",
                            client_name="Carmel Sanderson",
                            access_notes="RING BEFORE YOU TURN IN, dogs off chain")
    _visit(app, property_id, "08:30", job="Lame mare", status="cancelled")

    page = client.get(f"/farm/run?date={MONDAY}").data

    assert b"Willow Bend" in page
    assert b"Lame mare" in page
    assert b"CANCELLED" in page
    assert b'tr class="cancelled"' in page


def test_unlinked_stub_visit_never_appears_on_run_sheet(client, app):
    # DV-06 stub rows have no property_id: they cannot be driven to, so the
    # inner join keeps them off the run sheet without breaking the page.
    with app.app_context():
        get_db().execute(
            "INSERT INTO farm_visits (scheduled_at, duration_minutes, status)"
            " VALUES (?, 60, 'booked')",
            (f"{MONDAY}T10:30:00",),
        )
        get_db().commit()

    page = client.get(f"/farm/run?date={MONDAY}").data
    assert b"No farm visits booked for this day." in page


def test_two_appointment_kinds_are_kept_separate(client, app):
    # In-clinic consultation (one animal) on the same morning as a farm run.
    property_id = _property(app)
    _visit(app, property_id, "11:15", duration=120, job="Preg test", km=52)
    with app.app_context():
        db = get_db()
        client_id = db.execute(
            "INSERT INTO client (name) VALUES ('Ruby Owner')"
        ).lastrowid
        animal_id = db.execute(
            "INSERT INTO animals (client_id, name, species) VALUES (?, 'Ruby', 'dog')",
            (client_id,),
        ).lastrowid
        db.execute(
            "INSERT INTO consultations (animal_id, room, scheduled_at)"
            " VALUES (?, 1, ?)",
            (animal_id, f"{MONDAY}T09:00:00"),
        )
        db.commit()

    # The farm run sheet lists only farm visits, never clinic consultations.
    run_page = client.get(f"/farm/run?date={MONDAY}").data
    assert b"Kalinga Downs" in run_page
    assert b">Ruby<" not in run_page

    # The combined day schedule keeps the two kinds in separate sections.
    schedule = client.get(f"/api/schedule?date={MONDAY}").get_json()
    assert len(schedule["consultations"]) == 1
    assert len(schedule["farm_visits"]) == 1
    assert schedule["consultations"][0]["room"] == 1
    assert schedule["farm_visits"][0]["status"] == "booked"
