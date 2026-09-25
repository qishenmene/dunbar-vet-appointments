-- Database schema for the Dunbar Vet appointment system.
--
-- Domain tables are introduced by their respective feature branches / sprint
-- stories so schema changes are reviewed in pull requests.

PRAGMA foreign_keys = ON;

-- DV-01: client records (create and search). Update/deactivate arrive in DV-02.
CREATE TABLE IF NOT EXISTS client (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    phone       TEXT    NOT NULL DEFAULT '',
    address     TEXT    NOT NULL DEFAULT '',
    is_active   INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- DV-03: animals are recorded individually and belong to exactly one client.
-- Name and species are the required minimum (case study, section 4); breed
-- is optional. A client can have many animals, one, or none. The minimal
-- stub table on the DV-06 branch is superseded by this full record.
CREATE TABLE IF NOT EXISTS animals (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id   INTEGER NOT NULL REFERENCES client(id),
    name        TEXT    NOT NULL,
    species     TEXT    NOT NULL,
    breed       TEXT    NOT NULL DEFAULT '',
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- DV-05: rural properties belong to one client and hold the access details
-- the vet needs before leaving town (gates, chains, codes, ring-first rules).
-- Farm visits (DV-07) are booked against a property, not against an animal.
CREATE TABLE IF NOT EXISTS property (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id    INTEGER NOT NULL REFERENCES client(id),
    name         TEXT    NOT NULL,
    locality     TEXT    NOT NULL DEFAULT '',
    access_notes TEXT    NOT NULL DEFAULT '',
    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);
