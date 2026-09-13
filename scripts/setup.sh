#!/usr/bin/env bash
# Clean-checkout setup for macOS/Linux: venv, dependencies, config, database.
set -euo pipefail
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
[ -f .env ] || cp .env.example .env
flask --app run.py init-db
echo "Setup complete. Run ./scripts/run_dev.sh to start the app."
