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
# Claude Code stores each session's transcript at
# ~/.claude/projects/<repo path with / -> ->/<session-id>.jsonl - verified
# directly against this exact repo, not assumed. Used below to tell a
# genuine restart (transcript already exists - resume it) from a first-ever
# wake (doesn't exist yet - claim the ID fresh).
TRANSCRIPT_DIR="$HOME/.claude/projects/$(echo "$REPO" | tr '/' '-')"

command -v konsole >/dev/null 2>&1 || {
  echo "konsole not found - this script only knows how to launch konsole" >&2
  echo "on this machine. Fall back to the manual recipe: cd '$REPO' &&" >&2
  echo "AGENT_SLUG=<slug> claude --remote-control <codename> \"\$(cat agents/wake_prompt.txt)\"" >&2
  exit 1
}

wake_one() {
  local slug="$1" header codename tagline console_title rc_name
  local session_id_file session_id resume_flag
  if [ ! -d "$HERE/$slug" ]; then
    echo "skip: no agents/$slug/ (check agents/RULES.md's directive to list agents/*/AGENT.md)" >&2
    return 1
  fi
  # A stable per-agent session ID, generated once and reused forever, is
  # what makes a restart an actual --resume (full conversation memory)
  # instead of a blank session that only has STATUS.md/context to go on.
  # First wake ever for this agent: no transcript exists yet under this ID,
  # so claim it fresh with --session-id. Every wake after that: the
  # transcript's already there, so --resume picks the real conversation
  # back up.
  session_id_file="$HERE/$slug/.session_id"
  if [ ! -f "$session_id_file" ]; then
    python3 -c "import uuid; print(uuid.uuid4())" > "$session_id_file"
  fi
  session_id="$(cat "$session_id_file")"
  if [ -f "$TRANSCRIPT_DIR/$session_id.jsonl" ]; then
    resume_flag="--resume $session_id"
  else
    resume_flag="--session-id $session_id"
  fi
  # AGENT.md's first line is "# Codename (slug) — tagline" (tagline
  # optional). Pull both: the konsole tab stays just the codename (short,
  # readable at a glance in a narrow tab bar); the Remote Control / peer-
  # session name gets "Codename - tagline" so it's identifiable from
  # ListAgents/another device without the codename alone being ambiguous.
  # Falls back to the slug if AGENT.md's shape ever changes.
  header="$(head -1 "$HERE/$slug/AGENT.md" 2>/dev/null)"
  codename="$(echo "$header" | sed -E 's/^# (.*) \([^)]*\).*$/\1/')"
  tagline="$(echo "$header" | sed -E 's/^# .*\([^)]*\)( — (.*))?$/\2/')"
  console_title="${codename:-$slug}"
  rc_name="$console_title"
  [ -n "$tagline" ] && rc_name="$console_title - $tagline"
  echo "waking $slug ..."
  # --remote-control (named "Codename - tagline") so every agent is
  # reachable from another device by default, without a separate opt-in per
  # agent. The FIRST time this ever runs on a machine, Claude Code shows a
  # one-time "Enable Remote Control? (y/n)" confirmation in that konsole
  # window - a real interactive prompt, not scriptable. It's per-device,
  # not per-session: answer it once and every agent after that (this one
  # and future wakes) connects automatically, no reprompt.
  konsole --workdir "$REPO" --hold -e bash -c \
    "printf '\033]0;%s\007' '$console_title'; AGENT_SLUG=$slug claude --remote-control '$rc_name' $resume_flag \"\$(cat '$PROMPT_FILE')\"" &
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
