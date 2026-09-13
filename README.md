# Dunbar Veterinary Clinic — Appointment System

A web-based appointment system for Dunbar Veterinary Clinic (Boonah, QLD). It
replaces the front-counter A3 appointment book and the green farm diary with one
system that handles **both** kinds of work the practice books:

- **In-clinic consultations** — one animal, a fixed 15-minute slot on the
  consulting timetable, in one of the two consulting rooms.
- **Farm visits** — booked against a property, with a start time and an
  estimated duration in hours.

This repository is developed for **ISYS3001 Managing Software Development
(Assessment 2 & 3)** using Git/GitHub configuration management practices.
All client, staff and clinic data in the case study is fictional.

> Privacy note: per the assessment brief, this repository contains **no
> personal information or student IDs**. Team members are identified by their
> GitHub usernames only: `qishenmene`, `ST1418`, `weigua777`.

## Tech stack and why

| Concern        | Choice                          | Reason |
| -------------- | ------------------------------- | ------ |
| Language       | Python 3                        | Team skill, cross-platform |
| Web framework  | Flask                           | Small, simple, well documented |
| Storage        | SQLite (standard library)       | **Works fully offline** — the clinic's internet drops out regularly; no database server to install |
| Front end      | Server-rendered HTML (Jinja2)   | No build toolchain; runs from a clean checkout |
| Tests          | pytest                          | Automated behaviour tests required by the Definition of Done |
| Production WSGI| waitress                        | Pure-Python, runs on Windows and Linux |
| Hosting (VCS)  | GitHub (this repository)        | Version control, pull requests, CI |

The application runs **locally with no internet connection** after dependencies
are installed, which is a core requirement from the clinic owner.

## Prerequisites

- Python 3.11 or newer (`python --version`)
- Git
- No database server, cloud account or internet connection is required to run
  the app

## Quick start (clean checkout)

```bash
# 1. Clone
git clone https://github.com/qishenmene/dunbar-vet-appointments.git
cd dunbar-vet-appointments

# 2. Create a virtual environment and install dependencies
python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# macOS / Linux:
# source .venv/bin/activate
pip install -r requirements.txt

# 3. Configure environment (illustrative sample values only)
copy .env.example .env          # Windows: copy ; macOS/Linux: cp

# 4. Initialise the local database
flask --app run.py init-db

# 5. Run the development server
python run.py
```

Then open <http://127.0.0.1:5000>. The health check is at
<http://127.0.0.1:5000/healthz>.

Convenience scripts are provided in `scripts/` (`setup.bat` / `setup.sh`,
`run_dev.bat` / `run_dev.sh`, `run_prod.bat` / `run_prod.sh`).

## Running the tests

```bash
pytest
```

Tests run automatically for every pull request via GitHub Actions
(see `.github/workflows/ci.yml`).

## Configuration

All settings are environment-based and read through `config.py`. See
[`.env.example`](.env.example) for the full list with illustrative values and
[`docs/CONFIGURATION.md`](docs/CONFIGURATION.md) for details. No real secrets
are committed — `.env` is git-ignored.

## Documentation

- [Branching strategy & contribution workflow](docs/BRANCHING_STRATEGY.md)
- [Configuration management](docs/CONFIGURATION.md)
- [Deployment guide](docs/DEPLOYMENT.md)
- [Change log](CHANGELOG.md)

## Team workflow (summary)

1. Pick a story from the sprint backlog (story id, e.g. `DV-12`).
2. Create a branch from `develop` named `feature/DV-12-short-description`.
3. Make small commits using
   [Conventional Commits](docs/BRANCHING_STRATEGY.md#commit-message-convention).
4. Push and open a pull request into `develop`; another team member must review
   and approve it, and CI must pass, before merge.
5. Full rules are in [`docs/BRANCHING_STRATEGY.md`](docs/BRANCHING_STRATEGY.md)
   and the pull request template.

## Project status

Sprint 0 — project scaffold: application factory, environment-based
configuration, database initialisation, health check, automated test setup and
CI. Domain features (clients, animals, properties, appointments) are delivered
on story branches during the sprint.
