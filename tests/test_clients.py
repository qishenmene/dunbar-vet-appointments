"""Tests for DV-01: create clients and search by name."""


def test_create_client_persists(client):
    resp = client.post(
        "/clients/create",
        data={"name": "Martha Callaghan", "phone": "5550-0101", "address": "Stony Creek"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Martha Callaghan" in resp.data


def test_search_returns_only_matching_clients(client):
    client.post("/clients/create", data={"name": "Martha Callaghan"})
    client.post("/clients/create", data={"name": "Hugh McPherson"})

    resp = client.get("/clients/?q=call")

    assert b"Martha Callaghan" in resp.data
    assert b"<td>Hugh McPherson</td>" not in resp.data


def test_search_is_case_insensitive(client):
    client.post("/clients/create", data={"name": "Kalinga Downs Pastoral"})
    resp = client.get("/clients/?q=KALINGA")
    assert b"Kalinga Downs Pastoral" in resp.data


def test_search_with_no_matches_shows_empty_message_not_error(client):
    resp = client.get("/clients/?q=nobody")
    assert resp.status_code == 200
    assert b"No clients match" in resp.data


def test_empty_name_is_rejected(client):
    resp = client.post("/clients/create", data={"name": "   "}, follow_redirects=True)
    assert b"Client name is required" in resp.data
    assert b"<td>" not in resp.data
