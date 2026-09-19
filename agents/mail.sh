#!/usr/bin/env bash
# Send a brief message to another agent's mailbox.
#
# Usage:
#   agents/mail.sh <to> "<subject>" "<body>"
#   agents/mail.sh <to> "<subject>"              # body read from stdin
#   echo "body text" | agents/mail.sh <to> "<subject>"
#
# <to> is a slug - agents/<to>/ must exist. There is no "manager" mailbox:
# a file is not a notification. To reach the manager, call the
# PushNotification tool yourself for anything urgent, or write to your own
# agents/<slug>/STATUS.md for anything routine - see agents/RULES.md.
# Writes one file to mailbox/<to>/inbox/, named per RULES.md's mail-format
# rule: YYMMDDHHMMSS_<name>.md.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"

TO="${1:-}"; SUBJECT="${2:-}"
[ -n "$TO" ] || { echo "usage: agents/mail.sh <to> \"<subject>\" [\"<body>\"]" >&2; exit 2; }
[ -n "$SUBJECT" ] || { echo "a subject is required" >&2; exit 2; }

if [ "$TO" = "manager" ]; then
  echo "there is no manager mailbox - a file isn't a notification." >&2
  echo "urgent/needs-a-decision: call the PushNotification tool yourself." >&2
  echo "routine/FYI: write it to your own agents/<slug>/STATUS.md instead." >&2
  exit 2
fi
if [ ! -d "$HERE/$TO" ]; then
  echo "no such agent: $TO (no agents/$TO/ - check agents/RULES.md)" >&2
  exit 2
fi

INBOX="$REPO/mailbox/$TO/inbox"
mkdir -p "$INBOX"

FROM="${AGENT_SLUG:-$(whoami)}"
TS="$(date -u +%y%m%d%H%M%S)"
NAME_SLUG="$(echo "$SUBJECT" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' | sed 's/^-//;s/-$//' | cut -c1-50)"
FILE="$INBOX/${TS}_${NAME_SLUG}.md"

if [ $# -ge 3 ]; then
  BODY="$3"
else
  BODY="$(cat)"
fi

cat > "$FILE" << EOF
---
from: $FROM
to: $TO
subject: $SUBJECT
timestamp: $TS
---
$BODY
EOF

echo "sent -> mailbox/$TO/inbox/$(basename "$FILE")"
