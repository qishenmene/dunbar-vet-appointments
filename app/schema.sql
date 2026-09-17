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
