# In-flight state (kept current per RULES.md rule 11; rewritten 2026-09-29 11:15)

## Now
- 11:10 full export `--yes --resolve-jumps --update-baseline` on the HEADLESS
  browser (:9222). Stdout goes to the session scratchpad; the log is in data/logs/export/.
- If it's clean (ok=True, no `!` lines, 0 ambiguous):
  1. Commit `tools/coaching-bundle-export/coherence_baseline.json`.
  2. Mail Kart + Loom the new path.
  3. Update STATUS.
- Committed today: af5e637 (virtualized rows, widen cap), b64b345 (start_pmcp
  --headless), b3e0971 (phase 3b reliability + click-through tooltips/notifications).
- Raul was asked (in chat, ~10:40) whether "ALEX v01 zum Ausprobieren 2" or
  "Minimal Coaching for Development 2 for Raul" is the new workbench, and whether
  the export target should change. No answer yet.

## Blocked
- Questionnaire multiSubmit: waits for access to the real ALEX coaching (Kart 09-25).

## Key facts learned (don't re-derive)
- Unattended runs: `tools/start_pmcp.sh --headless`. A headed window gets no
  frames once the screen blanks, and every click then hangs. Headless ignores
  setWindowBounds for the viewport, so it launches at 12000px.
- After start_pmcp.sh the page is on Home. Open the coaching's Edit view first:
  click Coachings, then `_report_fetch.enter_edit_view(page, name)`.
- A page reload ENDS the PMCP session (lands on the login form).
  start_pmcp.sh re-logs in, reusing a running browser.
- Vaadin overlays (.v-tooltip, .v-Notification) intercept clicks and never fade
  headless. `_menu_nav.neutralize_tooltips` makes them click-through.
- Prefer polls to fixed waits in the nav code (daytime PMCP is slower).
- Closing an editor shows "The rule has been updated." / "The micro dialog
  decision point has been updated.": that's the known no-op re-save.
- The 14 ambiguous jumps: 12 point at empty anchor messages ("[not set]"), and
  2 (Welcome 77/90) at a duplicated real text.
- `--update-baseline` writes the baseline BEFORE phase 5, so the same run shows no drift.
- The exporter claims the browser lock itself.
- Monitoring must be off; if it's on, the export fails loudly. Never toggle it
  without Raul.
- Dev harness idea (scratchpad, not committed): run resolve_jumps_live against an
  old bundle. This takes ~8 min, versus ~20 min for a full export.

## Standing reminders
- Use mail ONLY in the plain `agents/checkmail.sh warden [--read <file>]` and
  `agents/mail.sh <to> "<subj>" "<body>"` forms. Never ask Raul about mail.
- Ask Raul only for real decisions. Re-login myself after an expiry.
- I may commit my own-scope files on main when tests pass
  (`.venv/bin/python -m unittest discover -s tests`). Kart pushes and pulls, never me.
- uids (md-NNN) are per-export positions. Use `path`/`dialogPath` across exports.
- Never edit other agents' files. Don't `export AGENT_SLUG`.
- `pkill -f <pattern>` kills my own shell if the pattern is in the command line.
  Use a `922[2]`-style regex.
