# In-flight state (kept current per RULES.md rule 11; rewritten 2026-09-29 11:15)

## 15:40: Raul runs the alex-live export HIMSELF (headed :9222, full program,
   --allow-noop-resaves). The first run was stopped (spirometry folder dropped),
   and the rerun started ~15:34 with the final-round retry (801a70a).
- When it finishes: check its log (data/logs/export/export_20260929-1534*.log), then
  mail Loom + Kart the json path for the r_ CSV steps.
- ROOT CAUSE FOUND (telemetry, Raul's 16:25 run): HEADED + a 12000px window on
  KDE/Wayland = a BLACK window with sporadic frames. Nothing intercepts the click
  (under = the item's own caption, otherActive=[]). The dropdowns just come late
  (late popup=1 at +3s), and clicks time out waiting for 'stable' (needs frames).
  The menu-state hypothesis is REFUTED.
  FIX TO BUILD: keep the real window screen-sized and emulate the wide viewport
  with CDP Emulation.setDeviceMetricsOverride(width=12000, ...) instead of
  Browser.setWindowBounds. Test on sandbox/alex-sandbox after Raul's run.
  Also done: _render_guard.py (pause + Enter + re-login + resume), a
  systemd-inhibit wrapper in export_coaching.sh, and a late popup now counts as opened.
- Phase 3b TODO: a live read of {'value': ''} = the jump dropdown is EMPTY = no jump
  set (Report '[not set]' was ambiguous with empty anchors). Resolve it to None
  ("no jump") instead of leaving it ambiguous. Seen on alex-live spirometry row 35.
- Phase 3b TODO 2: alex-live 'Attic / Andreas Test' row 5: the live read gives index 2
  = a command message ('increment-achievement main -4'), which is NOT among the Report's
  candidates. Check what the dropdown lists vs our `msgs` (non-decision nodes):
  command messages/events may be counted differently.
  LIKELY CAUSE (2nd case, 'Testing of streak concept' row 9 FALSE -> index 5,
  'set-achievement main 0'): the targets are COMMAND messages. Enrich builds the
  candidates from textByLang equality, and command nodes carry commandByLang, so
  they're never candidates. Fix: accept the live pick when the dropdown text matches
  that node's command/text, even if it isn't in the candidates.
- Phase 3b TODO 3: 'Attic / Calculate outcome of lottery...' row 11: the value IS set
  (a debug message) but the highlight = the blank top entry, so index -1. The target
  is probably on a later dropdown PAGE (Vaadin filterselect pages ~10 items).
  Match the item by the displayed value and page through (the status 'x-y/total'
  is in JUMP_POPUP_JS).
- (old) Menu flake: failures cluster on RE-opening the SAME top item right after closing
  it (spirometry -> sub-folder, weekly incentive -> Status...). Hypothesis: after
  Escape the item stays "active", so the click toggles it shut.
  wait_popup(tries=15) = only 1.5s. Telemetry committed (36bb85a) -> data/logs/
  menu_diag.jsonl. Read the records after the next run, then fix at the root.

## 13:23 update: Raul reassigned the alex-live export to LOOM (Kart 13:17)
- Loom has step-by-step instructions (mail 13:22). I support: jump on any failure log.
- Per-coaching baselines committed (935d7a8). Loom's first alex-live run uses
  --update-baseline, which creates coherence_baseline_alex-v01-zum-ausprobieren-2.json.
- Mine after Loom: a ~5 min ✕-close test on alex-sandbox (plan below). If it's clean,
  a read-only close lets alex-live exports include sender modals and jumps.

## (was TOP, Kart 12:21): read-only export of alex-live ("ALEX v01 zum Ausprobieren 2")
- Short names (RULES.md): alex-live = never changed; alex-sandbox = pile-up target;
  sandbox = Minimal Coaching for Development 2 for Raul.
- Blocked on the PMCP login (rejected since ~13:10). Raul may log in by hand in the
  visible browser on :9222 (it was launched with --no-login).
- Problem: closing editors with "Close" = a no-op re-save = a write. The exporter
  now auto-forces --no-modals and skips 3b on alex-live (2f89222). Plan:
  1. On alex-sandbox, open a sender rule editor, dismiss it via the window ✕
     (.v-window-closebox), and check that NO "has been updated" notification
     appears.
  2. If it's clean, give close_windows a read-only mode that uses ✕, and use it
     for alex-live.
  3. Export alex-live headed? No: after the login works, an unattended run
     means --headless (start_pmcp.sh --headless replaces the visible one only
     if you ask).
- Then mail Loom + Kart the path. After that: multiSubmit, read-only.
- Raul logged in by hand at ~13:30 (visible browser, :9222). I asked him in chat for
  the browser OK before driving it. Don't take it without that.

## Queued export-field requests (need live reads, not in the Report HTML)
- Smith: `$weekdays` multilingual variable values truncated (table cell read).
- Mirror: per-message `clearsCascade` flag (message editor checkbox). Mirror will
  batch it with an export-extension field list. Do one live pass, sandbox first.

## Now
- BEFORE export done:
  `data/exports/coaching_alex-v01-zum-ausprobieren_20260929-111706.json`
  (ok, 0 warnings, 14/14 jumps). The HTML-text fix was applied post-run, text
  fields only. Loom + Kart were mailed at 12:28, and Loom holds the browser for
  the 802-variant apply.
- NEXT: on Loom's done-mail, run the AFTER export with the same command:
  `export_coaching.sh --yes --resolve-jumps` (NO --update-baseline: the diff vs the
  baseline is wanted). Then mail Loom + Kart the path.
- Later: Smith's `$weekdays` truncation (read full multilingual values from the
  variable edit dialog, in `_variables_nav.py`).
- Mailbox listener: re-arm the Monitor on every expiry (Raul, 09-29).
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
