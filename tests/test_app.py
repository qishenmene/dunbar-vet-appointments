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
    """Domain rule: a day with no bookings is an empty schedule, not an error."""
    response = client.get("/api/schedule?date=2026-09-20")  # a Sunday
    assert response.status_code == 200
    assert response.get_json() == {
        "date": "2026-09-20",
        "consultations": [],
        "farm_visits": [],
    }
