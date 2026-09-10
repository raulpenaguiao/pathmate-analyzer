#!/usr/bin/env bash
# Runs the Pathmate Analyzer web portal locally, for development/testing.
# Creates a local virtualenv (.venv) and a .env file on first run, so this
# works out of the box on a fresh checkout. Run it from anywhere:
#   tools/run.sh
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."   # repo root

if [ ! -f .env ]; then
	echo "==> No .env found, creating one from .env.example - edit it before trusting the login." >&2
	cp .env.example .env
fi

if [ ! -x .venv/bin/pip ]; then
	# .venv/bin/pip only exists once ensurepip has actually succeeded, so this
	# also catches a partial/broken venv left over from a previous failed run
	# (python3 -m venv can leave a bin/python symlink behind even when it fails).
	echo "==> Creating virtualenv in .venv"
	rm -rf .venv
	if ! python3 -m venv .venv; then
		echo "Failed to create the virtualenv. On Debian/Ubuntu, install the venv module first:" >&2
		echo "    sudo apt install python3-venv" >&2
		exit 1
	fi
fi

echo "==> Installing/updating dependencies"
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt

bash ./deploy/generate_deploy_info.sh

PORT="${PORT:-8000}"
echo "==> Starting Pathmate Analyzer on http://localhost:${PORT}"
exec .venv/bin/python wsgi.py
