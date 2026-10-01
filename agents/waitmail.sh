#!/usr/bin/env bash
# Block until an agent has unread mail, then list it and exit.
#
# Usage:
#   agents/waitmail.sh [slug]
#
# Run it as a background Bash command (run_in_background). It has no time
# limit and exits only when mail is waiting (immediately, if some already
# is), so you get one notification per batch of mail instead of a
# half-hourly Monitor expiry. Read the mail with checkmail.sh, then start
# it again. slug defaults to $AGENT_SLUG.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SLUG="${1:-${AGENT_SLUG:-}}"
[ -n "$SLUG" ] || { echo "usage: agents/waitmail.sh <slug>  (or export AGENT_SLUG)" >&2; exit 2; }

INBOX="$HERE/$SLUG/mailbox/inbox"
[ -d "$INBOX" ] || { echo "no such mailbox: agents/$SLUG/mailbox/ (check agents/RULES.md)" >&2; exit 2; }

while [ "$(find "$INBOX" -maxdepth 1 -type f -name '*.md' | wc -l)" -eq 0 ]; do
  sleep 30
done

"$HERE/checkmail.sh" "$SLUG"
