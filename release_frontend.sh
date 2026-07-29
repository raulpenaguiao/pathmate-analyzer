#!/usr/bin/env bash
# Triggers the release_frontend CI/CD pipeline (.github/workflows/release_frontend.yml).
#
# Tag names must be unique in git, so this mints a fresh
# "release_frontend-<UTC timestamp>" tag every run instead of reusing one
# literal name - the workflow matches any tag starting with "release_frontend".
#
# This does NOT stage or commit your working-tree changes for you: commit
# what you want released first, then run this script to mark and push that
# commit as a release point.
set -euo pipefail

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
	echo "Not inside a git repository." >&2
	exit 1
fi

if [ -n "$(git status --porcelain)" ]; then
	echo "You have uncommitted changes. Commit or stash them first, then re-run this script." >&2
	git status --short
	exit 1
fi

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [ "$BRANCH" = "HEAD" ]; then
	echo "You're in a detached HEAD state. Check out a branch before releasing." >&2
	exit 1
fi

TIMESTAMP="$(date -u +%Y%m%d%H%M%S)"
TAG="release_frontend-${TIMESTAMP}"

echo "==> Marking current HEAD of '${BRANCH}' as a release with an empty commit"
git commit --allow-empty -m "Release frontend (${TIMESTAMP})"

echo "==> Tagging as ${TAG}"
git tag "$TAG"

echo "==> Pushing branch and tag to origin"
git push origin "$BRANCH"
git push origin "$TAG"

echo "==> Done. GitHub Actions should now be running the release_frontend workflow for tag ${TAG}."
