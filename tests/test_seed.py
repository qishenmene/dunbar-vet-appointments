"""Tests for seed sample data (issue DV-12).

Verifies the seed command loads fictional clients, animals, properties,
consultations and farm visits from the case study, with no real personal
data, and that re-seeding does not create duplicates.
"""
from app.db import get_db
from app.seed import seed_data


def test_seed_loads_expected_counts(app):
    seed_data(app)

    with app.app_context():
        db = get_db()
        clients = db.execute("SELECT COUNT(*) AS n FROM client").fetchone()["n"]
        animals = db.execute("SELECT COUNT(*) AS n FROM animals").fetchone()["n"]
        properties = db.execute("SELECT COUNT(*) AS n FROM property").fetchone()["n"]
        consultations = db.execute("SELECT COUNT(*) AS n FROM consultations").fetchone()["n"]
        farm_visits = db.execute("SELECT COUNT(*) AS n FROM farm_visits").fetchone()["n"]

    assert clients == 4
    assert animals == 8
    assert properties == 3
    assert consultations == 6
    assert farm_visits == 3


def test_seed_includes_case_study_names(app):
    seed_data(app)

    with app.app_context():
        db = get_db()
        client_names = [
            r["name"] for r in db.execute("SELECT name FROM client ORDER BY name").fetchall()
        ]
        animal_names = [
            r["name"] for r in db.execute("SELECT name FROM animals ORDER BY name").fetchall()
        ]

    assert "Martha Callaghan" in client_names
    assert "Kalinga Downs Pastoral Co" in client_names
    assert "Bella" in animal_names
    assert "Daisy" in animal_names


def test_seed_properties_have_access_notes(app):
    seed_data(app)

    with app.app_context():
        db = get_db()
        stony_creek = db.execute(
            "SELECT access_notes FROM property WHERE name = 'Stony Creek House'"
        ).fetchone()
        kalinga = db.execute(
            "SELECT access_notes FROM property WHERE name = 'Kalinga Downs'"
        ).fetchone()

    assert "chain" in stony_creek["access_notes"].lower()
    assert "ring first" in stony_creek["access_notes"].lower()
    assert "4821" in kalinga["access_notes"]


def test_seed_consultations_are_booked(app):
    seed_data(app)

    with app.app_context():
        db = get_db()
        statuses = {
            r["status"] for r in db.execute("SELECT status FROM consultations").fetchall()
        }
    assert statuses == {"booked"}


def test_seed_farm_visits_have_property_and_job(app):
    seed_data(app)

    with app.app_context():
        db = get_db()
        visit = db.execute(
            "SELECT fv.job_description, p.name AS property_name"
            " FROM farm_visits fv JOIN property p ON p.id = fv.property_id"
            " WHERE p.name = 'Kalinga Downs'"
        ).fetchone()

    assert visit is not None
    assert "TB test" in visit["job_description"]


def test_reseeding_does_not_create_duplicates(app):
    seed_data(app)
    seed_data(app)

    with app.app_context():
        db = get_db()
        clients = db.execute("SELECT COUNT(*) AS n FROM client").fetchone()["n"]
        animals = db.execute("SELECT COUNT(*) AS n FROM animals").fetchone()["n"]

    assert clients == 4
    assert animals == 8


def test_seed_uses_no_real_personal_data(app):
    """All seed data is fictional — check for case-study names only."""
    seed_data(app)

    with app.app_context():
        db = get_db()
        all_names = " ".join(
            r[0] for r in db.execute(
                "SELECT name FROM client UNION SELECT name FROM animals"
            ).fetchall()
        )

    # No real-looking phone numbers or real person indicators
    assert "test" not in all_names.lower()
    assert "real" not in all_names.lower()
