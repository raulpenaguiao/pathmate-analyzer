# In-flight state (updated continuously per RULES.md rule 11)

## Open thread: Loom's md-030 Randomisation Group retagging (2026-09-23)

- Loom asked (2026-09-21) for CDP browser time to inspect the
  "Randomisation Group" field's sub-editor DOM live, to write a new
  bootstrap-tagging mode in `rgroup_apply.py` (needed because `md-030#000`/
  `#001` lost their `r_` tags in Mason's spirometry rebuild and the
  existing add-flow has no path to tag a previously-untagged row).
- Checked at the time: no other agent's STATUS.md showed active browser
  use, and the CDP endpoint (127.0.0.1:9222) wasn't even responding — no
  tab was up. Told Loom the browser was free to take (mail
  `260923074210_browser-is-free-go-ahead.md`), plan = read-only inspection
  first (reference row, then md-030#000/#001 read-only), no writes until
  selectors are confirmed, and to come back for my review before any real
  write pass on the new nav code.
- 2026-09-23: Loom reported back — read_table_dense --dry-run clean, DOM
  confirmed the Randomisation Group sub-editor is a plain text input, and
  sent the new-nav-code diff (`tag_randomisation_group` +
  `--restore-from`/`--to-path`/`--bootstrap-text` mode) for review.
  Reviewed it (`git diff tools/rgroups-table/rgroup_apply.py`): swap is
  correct, new primitive follows existing conventions. Found one real
  gap: the bootstrap call site tags a row found by short-text-prefix
  match WITHOUT checking its Randomisation Group cell is actually blank
  first — could silently overwrite an existing tag on a bad match. Sent
  Loom the fix (check `rows[cand][gi].strip()` is empty before calling
  `tag_randomisation_group`, skip/error otherwise) — mail
  `260923090014_review-swap-looks-good-one-gap-in-the-bootstrap-pa.md`.
- 2026-09-23 (later): Loom applied the fix (implied, not explicitly
  confirmed in mail — Stage1_Push restore succeeded live, rows 0-2 all
  correctly tagged and adjacent). Stage3 blocked on something new: PMCP
  session (account alex-dev-2) keeps dropping to the login screen
  seconds into a run, across 3 re-logins, inconsistent with normal
  ~1-2h expiry and with only one CDP tab open. Checked all agents'
  STATUS.md — nobody else shows PMCP/CDP activity, and Mirror was never
  granted the browser (still queued). Not an agent-coordination
  conflict on our side. PushNotified Raul directly (mobile push came
  back "not sent — disabled in /config", unclear if desktop notice
  landed) asking whether he's logged into PMCP elsewhere on a non-CDP
  browser. Told Loom to keep holding off on further live attempts.
- 2026-09-23 (post-restart): VERIFIED the blank-field guard is in
  `rgroup_apply.py` (~L588-601, refuses if cand row already has a group).
  Closed. Re-asked Raul about the session-drop in chat.
- 2026-09-23 ~20:45: Mirror relayed that the PMCP docs are public at
  my.pathmate.app/pmcp-documentation/doc-6-0 (RULES.md now says to check
  them first). Found in `/sections/account`: admin in a coaching = coaching
  locked by that user; "Reset All Locks" logs everyone out of it. That's a
  documented mechanism that could explain the drops. No mention anywhere of
  one session per account. Mailed Loom and extended the question in STATUS.md.
- ~20:43: Loom independently found `/start-here`: "Only one coaching admin
  can work on the coaching intervention at a time." Added both doc quotes
  to the `_pmcp_safety.py` docstring as the suspected, unconfirmed cause.
  Uncommitted. The footguns list in the ALEX Rulebook artifact is not mine;
  add it there only once the cause is confirmed.
- **Waiting on**: Raul's answer on the session-drop cause. Loom is
  paused on Stage3 until then (Stage1_Push already succeeded). Browser
  is still nominally Loom's claim — Mirror queued behind them.
- If Raul's answer doesn't land and this recurs: worth checking
  whether PMCP is single-session-per-account (Loom's hypothesis) as a
  documented quirk for `_pmcp_safety.py` / the footguns list, once
  confirmed.
- If cut off before Loom's reply lands: re-check Loom's STATUS.md/mailbox
  first for progress that may not have generated mail to warden.

## Browser queue (2026-09-23)

1. **Loom** — md-030 Randomisation Group retag inspection (granted
   2026-09-23, see thread above). No confirmation yet they've started or
   finished; CDP port not currently answering, so no tab is actually up.
2. **Mirror** — wants read-only clicking on the *waterbot* coaching
   (explicitly NOT ALEX — Raul's instruction, it's the testbed) to see
   what Stage 4's `coaching.json` export is missing. Not urgent, Phase A
   done without it. Told them queued behind Loom, will ping when free.

When pinging Mirror: remember it's waterbot, not ALEX — don't let it
default to whatever coaching is already open.

## Standing reminders
- (2026-09-23) Auto-resume known next steps on wake unless blocked on
  someone's answer (RULES.md 4b). Kart owns `git pull` — don't pull myself.
- Don't hand Mirror the browser while the alex-dev-2 session-drop is
  undiagnosed: a second run on the same account would muddy the diagnosis.
- Do NOT `export AGENT_SLUG=...` — wake.sh already sets it at launch; each
  export was triggering an unwanted permission prompt for Raul (fixed in
  RULES.md 2026-09-23). If `echo $AGENT_SLUG` is ever genuinely empty,
  PushNotification the manager, don't self-fix with export.
- Never edit another agent's owned files directly (e.g. `rgroup_apply.py`
  is Loom's) — supply/extend the shared nav library
  (`tools/coaching-bundle-export/_*_nav.py`, `_pmcp_safety.py`,
  `_report_fetch.py`) and mail the exact swap instead.
- `inotifywait` is NOT installed on this box — the mailbox watcher must
  use a polling loop (see the Monitor command used this session), not
  `inotifywait -m` as RULES.md's example suggests.

## Task: export jump-to-message targets (for Mirror, taken 2026-09-24 06:25)
- Mirror mail 260924061824: coaching.json lacks decision-point "Jump to dialog
  message if TRUE/FALSE". Branches come only from Report HTML (enrich_bundle ->
  coaching_model._parse_branches), and the Report has no such rows.
- Agreed shape: per BRANCH (rule) `jumpMessageIfTrue`/`jumpMessageIfFalse` =
  node uid | {"raw","unresolved":true} | null. Told Kart.
- leaveDecisionPoint: not defined in the v6.0 docs, so I told Mirror it's unknown
  and not to guess (needs a live precedent).
- 06:39 UPDATE: no live run needed for most of it. The Report HTML HAS
  "Micro Dialog Message to jump to when TRUE/FALSE:" rows (per-language target
  text); _parse_branches just never read them. DONE (uncommitted):
  enrich_bundle._resolve_jump_target maps text to a node uid when unique, else
  {raw,candidates,unresolved}. Tested on the 0918 export with a stub: 22 resolved,
  14 unresolved (12 "[not set]" anchor msgs, 2 duplicate-text in md-004),
  md-049#003 -> #004/#006. 88/88 unittest (the runner is unittest, not pytest).
- Mailed Mirror (260924063906) the 3-part change for THEIR file app/coaching_model.py
  (DecisionBranch fields, _parse_branches lang_map rows, parse_bundle).
- Remaining: optional small live pass (read the branch filterselect comment) for
  the 14 unresolved, behind the coaching-lock question. Test scripts in the scratchpad.
- 07:06: Mirror landed their side (675e6f8, 4c5c47f). Real-code run matches
  the stub: 22/14. Wrote data/exports/..._20260918-103948_jumps.json (new file,
  nothing overwritten). The portal's attached bundle (08289c..., 09-14) is stale:
  unenriched, 0 branches, and md uids are positional so its md-049 is a different
  dialog. Told Mirror + Smith that re-attaching is Smith's/Raul's call.
  enrich_bundle.py + _pmcp_safety.py are uncommitted; waiting on Raul's go-ahead.
- 07:40 Smith: the 0918 export fails its coherence check. ROOT CAUSE: a partial sweep,
  md-060..md-089 all `top ... not found` (suspected menubar `►` overflow mid-run,
  NOT verified live). Hardening (uncommitted): _menu_nav.MenuOverflowError +
  _raise_missing_top; export_coaching retries once after re-widening on that
  error; coherence_check puts "PARTIAL EXPORT" first with ok=False; default
  filename gets _PARTIAL. Wrote a complete alternative,
  data/exports/..._20260917-174650_jumps.json (ok=True, 35/14 jumps). Told
  Smith and Mirror.
- Next live export: watch whether MenuOverflowError fires. That confirms the
  overflow hypothesis.
- 08:55 Mirror asked for DP rule nesting. It's in the Report: the DP rule table
  rows carry border-left-width = 20px*depth. enrich_bundle now emits
  depth + parentIndex (depth stack), defaulting to 0 until Mirror adds
  DecisionBranch.depth (mailed the regex). Verified md-054#037 0>1>2. Once Mirror
  lands it: regenerate data/exports/..._20260917-174650_jumps.json.
- 09:17 Regenerated the 0917 _jumps.json with real depth (Mirror 2749c6f). Told Mirror + Smith.
- 09:30 Raul: 1) commit OK -> 0686367. 2) The drops were session expiry during a late human reply, NOT a lock. Loom unblocked; queue Loom > Mirror (waterbot) > my fresh export.
- 09:40 Raul: uids are never static names. Added path/dialogPath to the exporter and an enrich backfill (uncommitted, new change). Regenerated the 0917 _jumps.json. Mailed all agents. Queue: Loom > Warden export > Mirror. Raul: 0917 is fine for testing meanwhile.
- 09:26 Mirror verified the 0917 _jumps.json in the engine (md-054 ACQ correct, no regressions) and DROPPED the waterbot slot. Queue: Loom > Warden export.
- 09-24 ~13:45: logged in myself (Raul's go). FOUND a hole: start_pmcp.sh said
  "already logged in" on a DEAD session. PMCP keeps the old page under a red
  "Session expired!" .v-Notification.system. Fixed start_pmcp.sh (detect it,
  reload, log in fresh; worked live incl. 2FA) and export_coaching's
  logged-in check. Most likely also why Loom's Stage3 half-wrote.
- 09-25 09:07: Raul ran export_coaching.sh himself. Phase 0 fetched the
  Report, then couldn't re-enter Edit. Screenshot: session expired again. Added
  _pmcp_safety.session_expired() + EXPIRED_HINT, used in both phase-0 exits
  (tested live: True). Monitoring toggle = Edit > Basic Settings and Modules.
  Hands off the browser while Raul drives. Uncommitted: path/dialogPath, expiry
  checks, start_pmcp.sh.
- 09-25 09:45 Raul: (a) implement the diagnosability fixes: timestamps, heartbeat,
  failure screenshot + state, cause-naming, run log. Logs go in a SEPARATE
  gitignored folder, not data/exports (use data/logs/export/). (b) Ask him less.
  Prefer no-approval actions or ONE standing approval. Timestamp every ask and
  self-resume after a logout (memory: minimize-manager-stalls).
- 10:00 Export 0925-093313 done. New checks: rows missing + node count != Report now fail. Browser handed to Loom (md-030: Stage3 has 2/6). Next: stale-table fix in the sweep (wait for the dialog title), then re-export.
- 10:25 Loom's gridText lead: fixed the enrich name+size ambiguity (nighttime Good Compliance had spirometry text) + TEXT != REPORT check (Timeless Greetings stale read). Regenerated the 0917 _jumps + 0925 export. Commit f2fc2ad. Mailed Mirror/Smith/Loom.
- 10:30 Smith: md-030 rows 3-4 have the Yes/No options bug = Loom's Stage3 source rows. Queue: Mason fix > Loom Stage3 > my sweep fix + re-export. Mailed both.
- 10:23 Raul took the browser to test the export himself. Mason + Loom told to hold.
- 10:35 MISTAKE: told Raul the browser was his, but Loom's rgroup_apply Stage3 was
  RUNNING (Loom hadn't read my hold). Caught by Raul. Letting Loom finish (safer than
  a half-write); Mason's fix now covers all 6 Stage3 rows. Queue: Loom > Raul export
  > Mason. LESSON: before granting the browser, check live processes
  (pgrep rgroup_apply|export_coaching|playwright), not just mail. Better: a
  browser lock file the tools claim/release themselves (to build).
