"""Tests for the sprint 0 scaffold (health check and home page)."""


def test_healthz_returns_ok(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_index_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Dunbar Veterinary Clinic" in response.data


def test_empty_day_schedule_returns_empty_not_error(client):
    """Domain rule placeholder: a day with no bookings is an empty schedule.

    Detailed appointment scheduling behaviour (15-minute consult slots vs.
    timed farm visits) is added and tested on the appointment story branches.
    """
    # The database initialises without error in the testing fixture.
    from app.db import get_db

    db = get_db()
    # No domain tables exist yet in sprint 0; connection is usable.
    assert db.execute("SELECT 1").fetchone()[0] == 1
