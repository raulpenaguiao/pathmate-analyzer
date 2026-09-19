#!/usr/bin/env bash
# Open a terminal window running an already-created agent's Claude Code
# session, using the one fixed wake prompt in agents/wake_prompt.txt.
#
# ============================================================================
# HUMAN-ONLY, same as createagent.sh and for the same reason. Starting
# another agent's session IS a form of agent spawning even when its
# identity already exists - an agent must never do this, for itself or on
# anyone else's behalf, even "to save you the typing". The safeguard here
# is the same interactive-terminal check createagent.sh uses; don't rely
# on that alone, treat it as an absolute rule.
# ============================================================================
#
# Usage:
#   agents/wake.sh <slug>     open one terminal for that agent
#   agents/wake.sh --all      open one terminal per existing agents/<slug>/
#
# Opens konsole (confirmed present on this machine) with --hold so the
# window stays open if claude exits or errors, rather than vanishing.
set -euo pipefail

if [ ! -t 0 ] || [ ! -t 1 ]; then
  cat >&2 << 'EOF'
refusing to run: this needs a real interactive terminal, and doesn't have
one. Same safeguard as createagent.sh - an agent's tool calls don't get a
real attached terminal, so this check is what stops an agent from waking
up another agent's session. If you are an agent reading this: don't work
around it, PushNotification the manager instead.
EOF
  exit 1
fi

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
PROMPT_FILE="$HERE/wake_prompt.txt"

command -v konsole >/dev/null 2>&1 || {
  echo "konsole not found - this script only knows how to launch konsole" >&2
  echo "on this machine. Fall back to the manual recipe: cd '$REPO' &&" >&2
  echo "AGENT_SLUG=<slug> claude \"\$(cat agents/wake_prompt.txt)\"" >&2
  exit 1
}

wake_one() {
  local slug="$1"
  if [ ! -d "$HERE/$slug" ]; then
    echo "skip: no agents/$slug/ (check agents/RULES.md's directive to list agents/*/AGENT.md)" >&2
    return 1
  fi
  echo "waking $slug ..."
  konsole --workdir "$REPO" --hold -e bash -c \
    "AGENT_SLUG=$slug claude \"\$(cat '$PROMPT_FILE')\"" &
  disown
}

if [ "${1:-}" = "--all" ]; then
  found=0
  for d in "$HERE"/*/; do
    slug="$(basename "$d")"
    [ -f "$d/AGENT.md" ] || continue   # skip non-agent entries in agents/
    wake_one "$slug" && found=$((found + 1))
  done
  [ "$found" -gt 0 ] || echo "no agents found under agents/ (create one with agents/createagent.sh first)" >&2
else
  SLUG="${1:-}"
  [ -n "$SLUG" ] || { echo "usage: agents/wake.sh <slug>   or   agents/wake.sh --all" >&2; exit 2; }
  wake_one "$SLUG"
fi
