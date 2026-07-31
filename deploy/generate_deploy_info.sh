#!/usr/bin/env bash
# Writes DEPLOY.md at the repo root, recording which commit produced this
# checkout. Called by run.sh for local dev, and by the release_frontend
# workflow (before rsync) so it travels with the synced code to the server.
# Never committed to git - it's only meaningful for the checkout that
# generated it.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

cat > DEPLOY.md <<EOF
# Deploy Info

- Commit: $(git rev-parse --short HEAD)
- Author: $(git log -1 --format=%an)
- Message: $(git log -1 --format=%s)

Generated automatically - do not edit by hand.
EOF
