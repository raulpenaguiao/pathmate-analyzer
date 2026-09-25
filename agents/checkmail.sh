#!/usr/bin/env bash
# List (or read) an agent's unread mail.
#
# Usage:
#   agents/checkmail.sh [slug]              # list unread, newest last
#   agents/checkmail.sh [slug] --read FILE  # print one message, archive it
#
# slug defaults to $AGENT_SLUG if set, else it's required.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SLUG="${1:-${AGENT_SLUG:-}}"
if [ -n "${1:-}" ] && [ "$1" = "--read" ]; then
  # allow: checkmail.sh --read FILE  (slug from $AGENT_SLUG)
  set -- "" "$@"
fi
[ -n "$SLUG" ] || { echo "usage: agents/checkmail.sh <slug> [--read FILE]  (or export AGENT_SLUG)" >&2; exit 2; }

INBOX="$HERE/$SLUG/mailbox/inbox"
READ_DIR="$HERE/$SLUG/mailbox/read"
[ -d "$INBOX" ] || { echo "no such mailbox: agents/$SLUG/mailbox/ (check agents/RULES.md)" >&2; exit 2; }
mkdir -p "$READ_DIR"

if [ "${2:-}" = "--read" ]; then
  TARGET="${3:-}"
  [ -n "$TARGET" ] || { echo "usage: agents/checkmail.sh $SLUG --read FILE" >&2; exit 2; }
  SRC="$INBOX/$(basename "$TARGET")"
  [ -f "$SRC" ] || { echo "not in agents/$SLUG/mailbox/inbox/: $(basename "$TARGET")" >&2; exit 2; }
  cat "$SRC"
  mv "$SRC" "$READ_DIR/"
  echo
  echo "(archived to agents/$SLUG/mailbox/read/)" >&2
  exit 0
fi

COUNT=$(find "$INBOX" -maxdepth 1 -type f -name '*.md' | wc -l | tr -d ' ')
if [ "$COUNT" -eq 0 ]; then
  echo "agents/$SLUG/mailbox/inbox/: empty - caught up."
  exit 0
fi

echo "agents/$SLUG/mailbox/inbox/: $COUNT unread"
echo
for f in $(find "$INBOX" -maxdepth 1 -type f -name '*.md' | sort); do
  from=$(sed -n 's/^from: //p' "$f" | head -1)
  subject=$(sed -n 's/^subject: //p' "$f" | head -1)
  ts=$(sed -n 's/^timestamp: //p' "$f" | head -1)
  printf '  %-16s  %-14s  %s\n' "$ts" "$from" "$subject"
  printf '    -> agents/checkmail.sh %s --read %s\n' "$SLUG" "$(basename "$f")"
done
