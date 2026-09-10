#!/usr/bin/env bash
# Triggers the release_frontend CI/CD pipeline (.github/workflows/release_frontend.yml).
#
# Tag names must be unique in git, so this mints a fresh
# "release_frontend-<UTC timestamp>" tag every run instead of reusing one
# literal name - the workflow matches any tag starting with "release_frontend".
#
# This does NOT stage or commit your working-tree changes for you: commit
# what you want released first, then run this script to mark and push that
# commit as a release point. Run it from anywhere: tools/release_frontend.sh
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."   # repo root

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
	echo "Not inside a git repository." >&2
	exit 1
fi

# Only tracked files matter here - untracked files (scratch notes, local
# reference material, etc.) never end up in the release commit anyway, so
# they shouldn't block it. Changes to tracked files won't be included either
# (this only tags the current HEAD), so flag those and ask before proceeding.
TRACKED_CHANGES="$(git status --porcelain --untracked-files=no)"
if [ -n "$TRACKED_CHANGES" ]; then
	echo "You have uncommitted changes to tracked files - they will NOT be part of this release:" >&2
	echo "$TRACKED_CHANGES" >&2
	read -r -p "Release the current HEAD anyway? [y/N] " CONFIRM
	case "$CONFIRM" in
		[yY]|[yY][eE][sS]) ;;
		*)
			echo "Aborted." >&2
			exit 1
			;;
	esac
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
