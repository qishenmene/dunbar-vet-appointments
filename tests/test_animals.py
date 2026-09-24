"""Tests for DV-03: animal records attached to clients."""

from app.clients import create_client
from app.db import get_db


def _client_id(app, name="Bridie Callaghan", phone="0417 884 260"):
    with app.app_context():
        return create_client(get_db(), name, phone)


def test_create_animal_persists_and_lists(client):
    client_id = _client_id(client.application)

    resp = client.post(
        "/animals/create",
        data={
            "client_id": client_id,
            "name": "Moss",
            "species": "Dog",
            "breed": "Kelpie x",
        },
        follow_redirects=True,
    )

    assert resp.status_code == 200
    assert b"Moss" in resp.data
    assert b"Dog" in resp.data
    assert b"Kelpie x" in resp.data
    assert b"Bridie Callaghan" in resp.data


def test_animal_persists_across_requests(client, app):
    """An animal saved in one request is still there in a new one."""
    client_id = _client_id(app)
    client.post(
        "/animals/create",
        data={"client_id": client_id, "name": "Tilly", "species": "Dog"},
    )

    resp = client.get(f"/animals/?client_id={client_id}")

    assert resp.status_code == 200
    assert b"Tilly" in resp.data


def test_animal_requires_existing_client(client):
    resp = client.post(
        "/animals/create",
        data={"client_id": "9999", "name": "Bracken", "species": "Dog"},
        follow_redirects=True,
    )

    assert b"Select an existing client" in resp.data
    assert b"Bracken" not in resp.data
    with client.application.app_context():
        rows = get_db().execute("SELECT COUNT(*) FROM animals").fetchone()[0]
    assert rows == 0


def test_animal_without_client_id_is_rejected(client):
    resp = client.post(
        "/animals/create",
        data={"name": "Sooty", "species": "Cat"},
        follow_redirects=True,
    )

    assert b"Select an existing client" in resp.data


def test_animal_name_is_required(client):
    client_id = _client_id(client.application)
    resp = client.post(
        "/animals/create",
        data={"client_id": client_id, "name": "  ", "species": "Cat"},
        follow_redirects=True,
    )

    assert b"Animal name is required" in resp.data


def test_animal_species_is_required(client):
    client_id = _client_id(client.application)
    resp = client.post(
        "/animals/create",
        data={"client_id": client_id, "name": "Sooty", "species": " "},
        follow_redirects=True,
    )

    assert b"Species is required" in resp.data


def test_list_only_shows_that_clients_animals(client, app):
    callaghan = _client_id(app, "Bridie Callaghan")
    petrie = _client_id(app, "R & M Petrie", "0427 118 553")
    client.post(
        "/animals/create",
        data={"client_id": callaghan, "name": "Moss", "species": "Dog"},
        follow_redirects=True,
    )
    client.post(
        "/animals/create",
        data={"client_id": petrie, "name": "Bess", "species": "Cattle"},
        follow_redirects=True,
    )

    resp = client.get(f"/animals/?client_id={callaghan}")

    assert b"Moss" in resp.data
    assert b"Bess" not in resp.data


def test_empty_client_returns_message_not_error(client):
    client_id = _client_id(client.application)
    resp = client.get(f"/animals/?client_id={client_id}")

    assert resp.status_code == 200
    assert b"No animals recorded" in resp.data


def test_invalid_client_id_renders_selector_without_error(client):
    resp = client.get("/animals/?client_id=not-a-number")

    assert resp.status_code == 200
    assert b"Select a client" in resp.data
