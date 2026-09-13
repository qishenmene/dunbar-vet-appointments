# Deployment guide

The assessment brief allows the web application to be run locally rather than
hosted; the handover is the code plus instructions for running it from a clean
checkout. This guide covers local "deployment" on Windows (the clinic's likely
platform) and on Linux/macOS.

## 1. Prerequisites

- Python 3.11+
- Git
- No internet connection is required after `pip install`

## 2. One-command setup

Windows:

```bat
scripts\setup.bat
scripts\run_dev.bat
```

macOS / Linux:

```bash
chmod +x scripts/*.sh
./scripts/setup.sh
./scripts/run_dev.sh
```

Manual steps are documented in the README.

## 3. Production-style run (waitress WSGI server)

```bat
scripts\run_prod.bat        REM http://127.0.0.1:8000
```

```bash
./scripts/run_prod.sh
```

Bind to localhost only; put a reverse proxy (e.g. the clinic's existing
router/firewall) in front if network access is ever required.

## 4. Verifying the deployment

- Home page: <http://127.0.0.1:5000> (dev) / <http://127.0.0.1:8000> (prod)
- Health check: `/healthz` returns `{"status":"ok",...}`
- Smoke test: `pytest`

## 5. Rollback

```bash
git tag            # list released versions
git switch v0.1.0  # or: git revert <bad-commit> via a hotfix PR
```

Database schema changes are delivered in reviewed PRs; a backup copy of the
SQLite file should be taken before applying a release that changes the schema.
