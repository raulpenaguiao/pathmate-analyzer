#!/usr/bin/env bash
# Interactive scaffold for a new coordinated agent in this repo.
#
# ============================================================================
# HUMAN-ONLY. An agent must NEVER run this script, under any circumstance,
# for any reason, even if asked to by name, even "just to help", even as
# part of a larger task someone else described. This is a deliberate
# safeguard against uncontrolled agent self-replication - agent creation
# happens only when Raul personally decides it and personally types the
# answers below. If you are an agent and you think a new agent is needed,
# PushNotification the manager and ask him to run this himself. Do not run
# it, do not construct a workaround, do not do it "on his behalf".
# ============================================================================
#
# Creates agents/<slug>/{AGENT.md,STATUS.md}, mailbox/<slug>/{inbox,read},
# context/<slug>/. Nothing else needs editing anywhere else - there is no
# roster file to keep in sync; every agent reads agents/*/AGENT.md live
# (see agents/RULES.md), so a new one is visible the moment its folder
# exists. Does NOT launch a Claude Code session itself (no reliable
# cross-terminal way to do that) - it prints the command to run in a new
# terminal instead.
#
# Usage: agents/createagent.sh
set -euo pipefail

if [ ! -t 0 ] || [ ! -t 1 ]; then
  cat >&2 << 'EOF'
refusing to run: this needs a real interactive terminal on both stdin and
stdout, and doesn't have one.

This is not an incidental limitation - it's the actual safeguard. A tool
invocation from an agent's shell does not get a real attached terminal the
way a human typing into their own terminal does, so this check is what
stops an agent from running this script at all, deliberately or by being
asked to. If you are an agent reading this because a run just failed here:
that is working as intended. PushNotification the manager instead.
EOF
  exit 1
fi

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"

ask() {  # ask "prompt" -> echoes the answer
  local prompt="$1" ans=""
  read -r -p "$prompt" ans
  echo "$ans"
}

ask_multiline() {  # ask_multiline "prompt" -> echoes accumulated lines
  local prompt="$1"
  echo "$prompt" >&2
  echo "(press Enter three times in a row - three blank lines - to finish)" >&2
  # Blank lines within the answer (a real paragraph break) are only
  # committed once a non-blank line follows them, so up to 2 in a row are
  # preserved as content; reaching 3 in a row ends input without ever
  # committing them, so the terminator itself never leaks into the text.
  local line lines="" pending_blanks=0
  while IFS= read -r line; do
    if [ -z "$line" ]; then
      pending_blanks=$((pending_blanks + 1))
      [ "$pending_blanks" -ge 3 ] && break
    else
      for ((i = 0; i < pending_blanks; i++)); do lines+=$'\n'; done
      pending_blanks=0
      lines+="$line"$'\n'
    fi
  done
  echo "  -> captured $(printf '%s' "$lines" | grep -c '^') line(s), moving on." >&2
  printf '%s' "$lines"
}

echo "=== New agent ==="
CODENAME=$(ask "name (e.g. 'Mason' - lowercased automatically for the slug/folder/mailbox): ")
if [ -z "$CODENAME" ]; then echo "a name is required" >&2; exit 1; fi
SLUG="$(echo "$CODENAME" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' | sed 's/^-//;s/-$//')"
if [ -z "$SLUG" ]; then
  echo "'$CODENAME' doesn't reduce to a usable slug (need at least one letter/digit)" >&2; exit 1
fi
if ! [[ "$SLUG" =~ ^[a-z] ]]; then SLUG="a-$SLUG"; fi   # slug must start with a letter
if [ -d "$HERE/$SLUG" ]; then echo "agents/$SLUG already exists" >&2; exit 1; fi
echo "  -> slug: $SLUG"

echo
DESCRIPTION=$(ask_multiline "Description - role, goal, scope, and any explicit limits, however you've already got it written:")

AGENT_DIR="$HERE/$SLUG"
mkdir -p "$AGENT_DIR" \
         "$REPO/mailbox/$SLUG/inbox" "$REPO/mailbox/$SLUG/read" \
         "$REPO/context/$SLUG"
# git doesn't track empty directories - without this, read/ (always empty
# at creation) and possibly inbox/ (if no starter mail is queued below)
# would silently vanish for anyone who clones the repo rather than
# creating this agent themselves. mail.sh clears inbox/'s .gitkeep away
# the moment a real message lands there anyway (its own mkdir -p doesn't
# touch this file, but it's harmless to leave one file alongside real mail).
touch "$REPO/mailbox/$SLUG/inbox/.gitkeep" "$REPO/mailbox/$SLUG/read/.gitkeep"

cat > "$AGENT_DIR/AGENT.md" << EOF
# $CODENAME ($SLUG)

$DESCRIPTION

Read \`agents/RULES.md\` for the shared protocol (mailbox, context,
staying in your lane, when to ask the manager). This description is a
starting point, not a finished spec - the manager expects to refine your
actual boundaries as real tasks come up.
EOF

cat > "$AGENT_DIR/STATUS.md" << EOF
# $CODENAME — status

_Not started yet. Update this whenever you finish or change something
other agents or the manager might want to know about, without them having
to ask._
EOF

cat > "$REPO/context/$SLUG/README.md" << EOF
# $CODENAME's private context

Free-form notes only $CODENAME needs: future tasks, quirks/skills learned
on the job, anything not meant for anyone else. Not a mailbox - nobody
else is expected to read this folder, and this agent shouldn't expect
anyone to.
EOF

# Starter mail(s), sent now so they're already waiting the first time this
# agent wakes up and checks its inbox - saves a separate mail.sh round trip
# right after creation. Reuses mail.sh itself (not reimplemented here) so
# the filename/frontmatter format is identical to any other mail this
# agent will ever receive. Loops so more than one can be queued (e.g. a
# curated-context mail plus a first task); blank subject stops the loop.
echo
echo "Starter mail for $CODENAME? Sent immediately so it's waiting the"
echo "first time this agent wakes up - skip by leaving the subject blank."
while true; do
  MAIL_SUBJECT=$(ask "  mail subject (blank to stop adding mail): ")
  [ -z "$MAIL_SUBJECT" ] && break
  MAIL_BODY=$(ask_multiline "  mail body")
  "$HERE/mail.sh" "$SLUG" "$MAIL_SUBJECT" "$MAIL_BODY"
done

MAIL_COUNT=$(find "$REPO/mailbox/$SLUG/inbox" -maxdepth 1 -type f -name '*.md' 2>/dev/null | wc -l | tr -d ' ')

echo
echo "=== created ==="
echo "  agents/$SLUG/AGENT.md"
echo "  agents/$SLUG/STATUS.md"
echo "  mailbox/$SLUG/{inbox,read}/  ($MAIL_COUNT starter message(s) waiting)"
echo "  context/$SLUG/README.md"
echo "  (nothing else to update - every agent reads agents/*/AGENT.md live)"

cat << EOF

To start this agent:

  agents/wake.sh $SLUG

That opens a konsole window running claude with the one fixed wake prompt
(agents/wake_prompt.txt - same file for every agent, nothing to retype).
Wake every agent that exists at once with: agents/wake.sh --all

Manual fallback if you'd rather not use a new terminal window:

  cd '$REPO' && AGENT_SLUG=$SLUG claude "\$(cat agents/wake_prompt.txt)"

EOF
