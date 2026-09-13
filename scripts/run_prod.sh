#!/usr/bin/env bash
# Serve the app with the waitress production WSGI server (macOS/Linux).
set -euo pipefail
# shellcheck disable=SC1091
source .venv/bin/activate
waitress-serve --host=127.0.0.1 --port=8000 run:app
