"""Tests for DV-02: update client details and make a client inactive."""

import pytest


def _create(client, name="Martha Callaghan", phone="5550-0101", address="Stony Creek"):
    client.post(
        "/clients/create",
        data={"name": name, "phone": phone, "address": address},
        follow_redirects=True,
    )
    from app.clients import search_clients
    from app.db import get_db

    row = search_clients(get_db(), name)[0]
    return row["id"]


def test_update_client_details(client):
    cid = _create(client)

    resp = client.post(
        f"/clients/{cid}/update",
        data={"name": "Martha Callan", "phone": "5550-0202", "address": "Boonah"},
        follow_redirects=True,
    )

    assert resp.status_code == 200
    assert b"Martha Callan" in resp.data
    assert b"5550-0202" in resp.data
    assert b"Boonah" in resp.data
    assert b"Martha Callaghan" not in resp.data


def test_update_does_not_change_other_clients(client):
    cid = _create(client, name="Martha Callaghan", phone="111")
    other = _create(client, name="Hugh McPherson", phone="222")

    client.post(
        f"/clients/{cid}/update",
        data={"name": "Martha Callan", "phone": "999", "address": "X"},
        follow_redirects=True,
    )

    resp = client.get(f"/clients/{other}/edit")
    assert b"Hugh McPherson" in resp.data
    assert b'value="222"' in resp.data


def test_update_with_empty_name_is_rejected_and_values_kept(client):
    cid = _create(client)

    resp = client.post(
        f"/clients/{cid}/update",
        data={"name": "   ", "phone": "000", "address": ""},
        follow_redirects=True,
    )

    assert b"Client name is required" in resp.data
    # original values untouched
    resp = client.get(f"/clients/{cid}/edit")
    assert b'value="Martha Callaghan"' in resp.data
    assert b'value="5550-0101"' in resp.data


def test_edit_page_prefills_current_values(client):
    cid = _create(client)

    resp = client.get(f"/clients/{cid}/edit")

    assert resp.status_code == 200
    assert b'value="Martha Callaghan"' in resp.data
    assert b'value="5550-0101"' in resp.data
    assert b'value="Stony Creek"' in resp.data


def test_deactivate_excludes_client_from_default_search(client):
    cid = _create(client)

    resp = client.post(f"/clients/{cid}/deactivate", follow_redirects=True)
    assert resp.status_code == 200
    # name still appears in the success flash, but not as a client table row
    assert b"<td>Martha Callaghan</td>" not in resp.data
    assert b"Inactive" not in resp.data.split(b"<table>")[1].split(b"</table>")[0]


def test_deactivated_client_can_still_be_found_with_all_flag(client):
    cid = _create(client)

    client.post(f"/clients/{cid}/deactivate", follow_redirects=True)
    resp = client.get("/clients/?all=1")

    assert b"Martha Callaghan" in resp.data
    assert b"Inactive" in resp.data
    assert b"Activate" in resp.data


def test_activate_restores_client_to_default_search(client):
    cid = _create(client)

    client.post(f"/clients/{cid}/deactivate", follow_redirects=True)
    assert b"Martha Callaghan" not in client.get("/clients/").data

    client.post(f"/clients/{cid}/activate", follow_redirects=True)
    assert b"Martha Callaghan" in client.get("/clients/").data


def test_deactivate_does_not_change_other_clients(client):
    cid = _create(client, name="Martha Callaghan")
    other = _create(client, name="Hugh McPherson")

    client.post(f"/clients/{cid}/deactivate", follow_redirects=True)

    resp = client.get("/clients/")
    assert b"Martha Callaghan" not in resp.data
    assert b"Hugh McPherson" in resp.data


@pytest.mark.parametrize("path", ["edit", "update", "deactivate", "activate"])
def test_unknown_client_returns_404(client, path):
    method = client.get if path == "edit" else client.post
    resp = method(f"/clients/9999/{path}")
    assert resp.status_code == 404
