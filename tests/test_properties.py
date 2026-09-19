"""Tests for DV-05: property records with access notes."""

from app.clients import create_client
from app.db import get_db
from app.properties import create_property


def _client_id(app, name="Bridie Callaghan", phone="0417 884 260"):
    with app.app_context():
        return create_client(get_db(), name, phone)


def test_create_property_persists_with_access_notes(client):
    client_id = _client_id(client.application)

    resp = client.post(
        "/properties/create",
        data={
            "client_id": client_id,
            "name": "Stony Creek",
            "locality": "Bunjurgen",
            "access_notes": "3 gates; last one has a chain, no code. Ring first.",
        },
        follow_redirects=True,
    )

    assert resp.status_code == 200
    assert b"Stony Creek" in resp.data
    assert b"Bunjurgen" in resp.data
    assert b"chain, no code" in resp.data


def test_property_requires_existing_client(client):
    resp = client.post(
        "/properties/create",
        data={"client_id": "9999", "name": "Kalinga Downs", "locality": "Coulson"},
        follow_redirects=True,
    )

    assert b"Select an existing client" in resp.data
    assert b"Kalinga Downs" not in resp.data


def test_property_name_is_required(client):
    client_id = _client_id(client.application)
    resp = client.post(
        "/properties/create",
        data={"client_id": client_id, "name": "  ", "locality": "Milford"},
        follow_redirects=True,
    )

    assert b"Property name is required" in resp.data


def test_list_only_shows_that_clients_properties(client, app):
    callaghan = _client_id(app, "Bridie Callaghan")
    petrie = _client_id(app, "R & M Petrie", "0427 118 553")
    client.post(
        "/properties/create",
        data={"client_id": callaghan, "name": "Stony Creek", "locality": "Bunjurgen"},
        follow_redirects=True,
    )
    client.post(
        "/properties/create",
        data={"client_id": petrie, "name": "Kalinga Downs", "locality": "Coulson"},
        follow_redirects=True,
    )

    resp = client.get(f"/properties/?client_id={callaghan}")

    assert b"Stony Creek" in resp.data
    assert b">Kalinga Downs</td>" not in resp.data


def test_empty_client_returns_message_not_error(client):
    client_id = _client_id(client.application)
    resp = client.get(f"/properties/?client_id={client_id}")
    assert resp.status_code == 200
    assert b"No properties recorded" in resp.data


def test_search_properties_by_name_across_clients(client, app):
    callaghan = _client_id(app, "Bridie Callaghan")
    petrie = _client_id(app, "R & M Petrie", "0427 118 553")
    client.post(
        "/properties/create",
        data={"client_id": callaghan, "name": "Stony Creek", "locality": "Bunjurgen"},
        follow_redirects=True,
    )
    client.post(
        "/properties/create",
        data={"client_id": petrie, "name": "Kalinga Downs", "locality": "Coulson"},
        follow_redirects=True,
    )

    resp = client.get("/properties/search?q=kalinga")

    assert b"Kalinga Downs" in resp.data
    assert b"Coulson" in resp.data
    assert b"R &amp; M Petrie" in resp.data
    assert b"Stony Creek" not in resp.data


def test_search_no_matches_shows_message(client):
    resp = client.get("/properties/search?q=nowhere")
    assert resp.status_code == 200
    assert b"No properties match" in resp.data


def test_update_property_changes_access_notes(client, app):
    client_id = _client_id(app)
    with app.app_context():
        property_id = create_property(
            get_db(), client_id, "Stony Creek", "Bunjurgen", "Old note"
        )

    resp = client.post(
        f"/properties/{property_id}/update",
        data={
            "name": "Stony Creek",
            "locality": "Bunjurgen",
            "access_notes": "Updated: ring Sean Duggan on arrival.",
        },
        follow_redirects=True,
    )

    assert b"Updated: ring Sean Duggan" in resp.data
    assert b"Old note" not in resp.data


def test_update_unknown_property_returns_404(client):
    resp = client.post(
        "/properties/9999/update",
        data={"name": "X", "locality": "", "access_notes": ""},
    )
    assert resp.status_code == 404


def test_delete_property_removes_it(client, app):
    client_id = _client_id(app)
    with app.app_context():
        property_id = create_property(
            get_db(), client_id, "Stony Creek", "Bunjurgen", "gate code 4417"
        )

    resp = client.post(
        f"/properties/{property_id}/delete", follow_redirects=True
    )

    assert resp.status_code == 200
    assert b">Stony Creek</td>" not in resp.data
    with app.app_context():
        rows = get_db().execute("SELECT COUNT(*) FROM property").fetchone()[0]
    assert rows == 0
