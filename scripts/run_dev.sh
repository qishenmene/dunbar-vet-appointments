#!/usr/bin/env bash
# Start the Flask development server (macOS/Linux).
set -euo pipefail
# shellcheck disable=SC1091
source .venv/bin/activate
python run.py
