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

-- DV-06: in-clinic consultations are fifteen-minute slots in room 1 or
-- room 2. Every consultation starts in the 'booked' state; cancelling keeps
-- the row so the appointment book retains a record of cancelled consultations.
CREATE TABLE IF NOT EXISTS consultations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    animal_id INTEGER NOT NULL REFERENCES animals(id),
    room INTEGER NOT NULL CHECK (room IN (1, 2)),
    scheduled_at TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL DEFAULT 15,
    status TEXT NOT NULL DEFAULT 'booked' CHECK (status IN ('booked', 'cancelled')),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Farm visits: minimal rows so the day schedule can show both appointment
-- kinds; the farm visit story owns their full behaviour and fields.
CREATE TABLE IF NOT EXISTS farm_visits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scheduled_at TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL DEFAULT 60,
    status TEXT NOT NULL DEFAULT 'booked' CHECK (status IN ('booked', 'cancelled')),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
