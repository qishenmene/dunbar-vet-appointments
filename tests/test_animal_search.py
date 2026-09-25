"""Tests for DV-04: search animals by name across all clients."""

from app.animals import create_animal
from app.clients import create_client
from app.db import get_db


def _setup(app):
    """Two clients, each with an animal called Ruby (the practice has many)."""
    with app.app_context():
        kelso = create_client(get_db(), "Mrs Kelso", "0413 900 001")
        hendren = create_client(get_db(), "Hendren", "0407 883 122")
        create_animal(get_db(), kelso, "Ruby", "Cat")
        create_animal(get_db(), hendren, "Ruby", "Dog")
        create_animal(get_db(), hendren, "Pip", "Dog")
    return kelso, hendren


def test_search_returns_every_match_with_owners(client, app):
    _setup(app)

    resp = client.get("/animals/search?q=Ruby")

    assert resp.status_code == 200
    # Both Rubys are returned and each is shown with its owner.
    assert resp.data.count(b">Ruby<") == 2
    assert b"Mrs Kelso" in resp.data
    assert b"Hendren" in resp.data


def test_search_shows_owner_phone(client, app):
    """Reception needs the owner's contact while the caller waits."""
    _setup(app)
    resp = client.get("/animals/search?q=Ruby")
    assert b"0413 900 001" in resp.data


def test_search_matches_substring_case_insensitively(client, app):
    _setup(app)
    resp = client.get("/animals/search?q=RUB")
    assert resp.data.count(b">Ruby<") == 2


def test_search_with_no_matches_shows_message(client, app):
    _setup(app)
    resp = client.get("/animals/search?q=zzz")
    assert resp.status_code == 200
    assert b"No animals match" in resp.data
    assert b">Ruby<" not in resp.data


def test_blank_search_prompts_without_listing(client, app):
    _setup(app)
    resp = client.get("/animals/search?q=")
    assert resp.status_code == 200
    assert b"Type part of an animal" in resp.data
    assert b">Ruby<" not in resp.data


def test_inactive_clients_animals_are_excluded(client, app):
    """Animals of deactivated clients should not surface for new bookings."""
    _setup(app)
    with app.app_context():
        get_db().execute("UPDATE client SET is_active = 0 WHERE name = 'Mrs Kelso'")
        get_db().commit()

    resp = client.get("/animals/search?q=Ruby")

    assert resp.data.count(b">Ruby<") == 1
    assert b"Mrs Kelso" not in resp.data
