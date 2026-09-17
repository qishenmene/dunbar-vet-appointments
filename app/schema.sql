-- Database schema for the Dunbar Vet appointment system.
--
-- Domain tables are introduced by their respective feature branches /
-- sprint stories so schema changes are reviewed in pull requests.

PRAGMA foreign_keys = ON;

-- Animals that appointments are booked for (DV-06). Full client and animal
-- record management is delivered by its own story and can extend this table.
CREATE TABLE IF NOT EXISTS animals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    species TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- In-clinic consultations: fifteen-minute slots in room 1 or room 2 (DV-06).
-- Every consultation starts in the 'booked' state; cancelling keeps the row
-- so the appointment book retains a record of cancelled consultations.
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
