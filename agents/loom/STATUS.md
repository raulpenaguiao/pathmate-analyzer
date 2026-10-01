# Loom — status

## 2026-10-01 ~12:00 — CURRENT: task 2 PAUSED, Raul exporting
- Task 2 (Raul's CSV rgroups_generated_260930163339.csv -> alex-sandbox) was
  STOPPED after 2 variants, nothing written (Timeless Greetings rows 0-9 read
  back unchanged). Bug 1 FIXED (committed): "stray copy" reuse would overwrite
  real repeated rows (row 9 = row 1). Bug 2 OPEN: at 1400px the message editor's
  "text (with placeholders)" row wasn't found; dismiss() then opened "Edit
  comment:", which is still open in the browser (Cancel didn't close it).
- Proposed to Raul (waiting): close via X -> 1 supervised variant with --debug
  on Timeless Greetings -> then the full 793. Raul is exporting now: DO NOT
  touch the browser until he says so.
- Masculine CSV: Raul chose Sonnet. Plan: prefilter (139 unique candidates of
  713 unique / 1325 texts, alex-live 143134) -> manager runs the Sonnet batch
  script -> I merge into one CSV of all rows + flags. The script isn't written yet.

## 2026-09-30 ~16:40
- **Every r_ step now takes its input file explicitly** (Raul): prepare TABLE,
  expand REQUESTS [--resume GENERATED], apply --csv (required). The pipeline
  passes the printed files along. Commit 2703975.
- **Dupcheck done** (Kart 135004): rgroup_dupcheck.py; pools = consecutive runs;
  cond=different labelled. Reports for alex-live/alex-sandbox in data/rgroups/
  dupcheck_*.md; Kart mailed.
- **Advisor page**: Herald's v5 (commands 'See it run') checked, accurate. Smith
  was asked for portal screenshots, to go to Herald.
- Task 2 still POSTPONED (Raul makes the CSVs first). No API runs by Loom.
- Raul: masculine copy of rgroups_table_260930160010.csv (alex-sandbox, 424 rows)
  -> `data/rgroups/rgroups_table_260930160010_masculine.csv`. Only 3 ro-RO cells
  had gender alternations (sigur/ă, implicat/ă, consecvent(ă)); every other
  user-directed form was already masculine, and the feminine forms modify
  feminine nouns. Dupcheck: ro-RO-holds-English check added (43acb02).

## 2026-09-30 ~12:40
**alex-live r_ CSVs DONE**: `rgroups_generated_260930123725.csv`, 1314 rows /
159 pools / 125 groups: 1312 ok, 2 dup (r_EveningGreetings), 0 failed. Kart +
Herald mailed. Fix: expand's max_tokens gets +2500 headroom (thinking tokens
count against it; long pools came back empty).
**rgroup_apply: no window resizing anymore** (Raul 09-30 via Warden): widen,
restore and PMCP_WIDE removed; relies on _menu_nav overflow handling. Untested live.
**Task 2 POSTPONED by Raul (09-30 ~15:00)**: he'll create the CSV files himself
first. Nothing was written; the browser was released (Warden + Kart told).
Don't restart it until Raul says so. NOW: the dupcheck tool (Kart 135004, no API).
(old:) task 2 = alex-sandbox apply, 802, `--csv rgroups_generated_260929093415.csv`.
Waiting for the browser: Raul's export is running, so NO browser use until he
or Warden frees it. The .env login WORKS again (Warden 122808; 09-29's rejection
was temporary), so start_pmcp.sh re-logs in. Then, in one go: enter_edit.py ->
apply (the session dies after ~30 min idle).

**~16:57 alex-live r_ steps:** export `coaching_alex-v01-zum-ausprobieren-2_20260929-162548.json`
(Raul ran it). Report: 138 r_ groups, 538 msgs, 175 pools, 159 thin ->
`rgroups_table_260929165622.csv`; requests 159 calls / 1314 variants
(`rgroups_requests_260929165622.csv`). Compared with alex-sandbox: +53 groups
(weekly-incentive weeks Streak/Lottery/Value Retention, Morning greetings +
sleep, ...), -4 (GoodOverallCompliance_Stage1-3, NighttimeMonitoring_Stage3_Push).
An "Attic" dialog has 3 groups. **Expand PARTIAL**: `rgroups_generated_260929170725.csv`
has 284 ok + 2 dup, 37 pools complete. The rest failed with 400 "specified API
usage limits ... regain access 2026-10-01 00:00 UTC" (spend cap). The guard
regex missed this wording; FIXED ("usage limit"). **Needs Raul**: raise the
cap or wait. Then: `rgroup_expand.py --resume --limit 122` (122 pools / 1028
variants). It must run while the alex-live requests/generated files are the
LATEST in data/rgroups/. Kart + Herald mailed.
Task 2 must keep --csv rgroups_generated_260929093415.csv!

**UPDATE (Warden 132840): Raul runs the alex-live export HIMSELF. Do NOT
start it. Wait for Warden's mail with the .json path, then run report ->
prepare -> expand (no apply) and mail Kart + Herald. Mine never started.**

## 2026-09-29 ~15:30 — (superseded) alex-live export plan
Warden's handover 132258: Raul logs in by hand in the HEADED Chromium :9222
(the .env login is still rejected; keep the screen on for ~25 min). Then
IMMEDIATELY: `.venv/bin/python agents/loom/context/enter_edit.py "ALEX v01 zum Ausprobieren 2"`
then `tools/coaching-bundle-export/export_coaching.sh --yes --update-baseline`
(no --resolve-jumps). The output MUST say "...is the CLEAN reference coaching
... read-only run", else Ctrl-C. Monitoring must already be off (never toggle
it). Then report -> prepare -> expand on the new json (NO apply), and mail
Kart + Herald. At ~15:30 the browser showed 1 tab, not logged in, so I'm
waiting for Raul's login.

## 2026-09-29 ~14:30 — two queued tasks
**Coaching names (RULES.md 'PMCP coachings'):** alex-live = 'ALEX v01 zum
Ausprobieren 2', EXPORT ONLY, never write. alex-sandbox = 'ALEX v01 zum
Ausprobieren', the task-2 target. sandbox = 'Minimal Coaching for Development 2
for Raul'. rgroup_apply was audited: no coaching-name substring match;
assert_expected_coaching is exact and refuses alex-live.
**Task 3 (Kart 122140):** when Warden mails the alex-live export path, run
report -> prepare -> expand on it (NO apply). Mail Kart + Herald the file
names + counts, and flag big differences from alex-sandbox (89 groups / 102
thin pools).
**Task 2 MUST pin its CSV** now that data/rgroups/ will hold alex-live
files too: `rgroup_apply.py --limit 802 --csv rgroups_generated_260929093415.csv`
(new --csv flag). Still blocked on the PMCP login.

## 2026-09-29 ~13:20 — BLOCKED: PMCP login rejected
The session expired again while idle (~30 min). start_pmcp.sh then got
"The username/password combination is unknown to the system" with the same
.env. Not retrying (lockout risk). Asked Raul (terminal), Warden, Kart.
Once fixed, run in ONE go: start_pmcp.sh --headless &&
`.venv/bin/python agents/loom/context/enter_edit.py` (finds the logged-in tab, closes dead tabs, opens Edit view +
Micro Dialogs) && the apply. Idle gaps kill the session.
Warden (105319): not from their side; the account changed server-side after
12:40. Neither of us retries until Raul confirms. Herald's explainer reviewed
(3 fixes sent; v2 is up). Owes Herald: the diff numbers + the comparison
artifact link after task 2. Kart routed the typo to Mason (workbench); 0
generated variants carry it.

## 2026-09-29 ~12:45 — (earlier) RESUME notes
Warden handed over the browser (BEFORE export `..._20260929-111706.json`).
First apply attempt exited safely with 0 writes: the PMCP session had expired
(all tabs "Session expired!"). Re-logged in with `tools/start_pmcp.sh
--headless` (OK, page on Home). NEXT: click Coachings ->
`_report_fetch.enter_edit_view(page, "ALEX v01 zum Ausprobieren")`, then
rerun the apply command below (log to data/logs/rgroup_apply_20260929.log).
Watch it with a Monitor that greps for `  ! ` errors and stop it if they
pile up. The browser has 5 tabs, 4 of them on the login form; apply picks
the md-menu tab, or else tab 0. Herald's mail 260929102842 (review the
r_ explainer draft + the live typo `$particpantName` in
r_TimelessGreetings) is still unanswered.

## 2026-09-29 ~10:00 — task 2 (live apply, Raul's exception)

Kart 260929081811 + 081847, TASKS.md top: apply ALL 802 ok variants of
`rgroups_generated_260929093415.csv` to the ALEX v01 sandbox in ONE run, no
sample batch. Order: Warden's BEFORE export -> browser hand-off to me ->
`PMCP_CDP=http://127.0.0.1:9222 .venv/bin/python tools/rgroups-table/rgroup_apply.py --limit 802`
(claims the browser lock) -> Warden's AFTER export -> I diff before/after
.json -> NEW artifact for Raul (counts per pool, examples, surprises) ->
link to Kart. Stop and tell Kart if apply starts failing (apply itself
doesn't stop on errors: watch the output and TaskStop). The dry-run
plan is checked: 802 across 41 dialogs. Heads-up sent to Kart + Mason: 6 new
Stage3 rows in v02 will inherit the Yes/No bug. Mason (102800): fine,
the sandbox gets reset and the Yes/No fix was dropped; the workbench build
enters the options correctly (noted in context/). **Waiting on Warden's
hand-off.** Mailbox listener: Monitor, re-arm every 30 min.

## 2026-09-29 ~00:20 — CURRENT: r_ steps 1-3 on the clean export

Input: Warden's clean export `coaching_alex-v01-zum-ausprobieren_20260925-161248.json`
(still the newest). Step 1 report: 89 r_ groups (95 incl. r1-3 and
IntroductionOfWeeklyIncentive_*, matches Warden's count), 424 msgs,
117 pools, 102 thin -> `rgroups_table_260929001638.csv`. Step 2 prepare:
102 API calls / 804 variants -> `rgroups_requests_260929001638.csv`.
**09:24: expand DONE** -> `data/rgroups/rgroups_generated_260929092409.csv`
(+ `expand_prompts_260929092409.txt`). 102/102 pools, 798/804 variants ok.
Not ok (apply skips them): 2 duplicates rejected by the new post-check
(Evening Greetings "Good evening! 🌙" repeats an existing en-GB;
one CompassionateFeedbackAndQueryMedicalHelp ro-RO repeats a sibling),
and 4 empty rows in r_ConfirmThatClinicVisitWillBeRescheduled (reply cut
off mid-JSON, 5/9 salvaged). Facts sent to Herald + Kart.
**09:34 FINAL: `--resume` refilled the 4 clinic-visit rows ->
`rgroups_generated_260929093415.csv`, 802/804 ok (2 duplicates flagged).
Committed ("r_ expand: abort on bad key...", not pushed; Kart pushes). Herald has the final numbers
+ a Stage3 correction (clean export: v02 rows 3-6 tagged = 4/6, row 15
stray; missing "close by", "access to").**
**Built (Raul OK'd)**: `rgroup_expand.py` now aborts the run on
account-level errors (401/403, no credits, 429 after 3 backoff retries;
5xx retried too), writes what's done, marks the rest "failed: not run", and
exits 1. `--resume --limit N` calls only the pools the latest generated file
lacks or left unfilled (partial pools: just the missing count, salvaged
wordings added to "existing") and writes a new merged file. Tested offline
with a mocked API (scratchpad test_expand_guard.py). On the real 09-29 file,
--resume would do 1 call: the clinic-visit pool, 4 variants. Not run yet.
(Earlier: Raul updated the key ~00:30.)
(Earlier:) **Step 3 expand BLOCKED: the ANTHROPIC_API_KEY in `.env` gets HTTP 401
Unauthorized on every call** (key revoked/expired). I stopped the run
after ~60 failures. No generated file was written, so there's nothing to
clean up. **Needs Raul: a valid key in `.env`.** Then rerun:
`.venv/bin/python tools/rgroups-table/rgroup_expand.py --limit 102`
(it picks up requests_260929001638 automatically). Step 4 apply:
dry-run/offline only; still no live PMCP writes (Stage3 stopped per Raul).
Next after expand: check output (duplicate check, counts), send Herald
the facts for the advisor artifact, update Kart.

## 2026-09-25 ~09:50 — CURRENT

**Stage3 STOPPED; no live PMCP writes until further notice** (Raul via
Kart, 260925094324; a test workbench coaching is coming). Last live read of
the v02 spirometry dialog: rows 3-6 are Stage3 (handy, within reach, with
you, nearby). Rows 3-6 have the one-line Yes/No options bug; Mason is
fixing it. Row 15 is a stray unedited copy of "handy" tagged Stage3, from
a failed attempt. Still missing: "close by" and "access to". This
morning's runs also fixed rgroup_apply.py: the first row of a pool counts
as in the pool (was a false "not adjacent"), plus the en_cell_matches fix
below. I missed Warden's hold mails while my run was going, and Raul waited
for the browser. Next time: check mail right before any live run.

**16:45 update**: pushed b35d0a1; committed e23355e (expand dedup + browser
lock, not pushed yet). Waiting on Warden's clean export (~16:50, the 093313
one has stale Timeless Greetings rows and can't be repaired offline).
Rehearsed steps 1-3 (expand dry-run) on 093313: 87 groups / 421 msgs /
118 pools / 103 thin -> 103 API calls, 831 variants. The real run = same
3 commands on the clean file, expand --limit 103.

**Today**: commit+push -> rerun r_ steps 0-3 (report/prepare/expand) for the
advisor CSV, apply dry-run/offline only; send Herald the facts; add a
duplicate-wording check to expand (prompt + post-check).

## 2026-09-25 morning — last-24h summary for Raul

**State of r_PromptForSpirometry_Stage3** (verified from Warden's fresh
export `data/exports/coaching_alex-v01-zum-ausprobieren_20260925-093313.json`):
v02 spirometry dialog rows 0-2 = Stage1_Push (done), rows 3-4 = Stage3
("handy", "within reach"), rows 5-12 untagged. No duplicates or stray rows.
**4 of 6 Stage3 variants still to add**: "close by", "with you", "access to",
"nearby".

**Last 24h:**
- Session drops: plain expiry, not a lock (Raul via Warden). PMCP docs
  lead on per-coaching admin locks passed to Warden (now in _pmcp_safety).
- Stage3 run 1: 0 writes, menubar overflow. Fixed a bug in rgroup_apply.py:
  it widened the window before switching to Micro Dialogs; it now switches
  first, then widens and checks for no `►`.
- Stage3 run 2: tagged the canonical row + added "within reach". The rest of
  the output was garbage, caused by a dead session (per Warden) AND a real
  bug found today:
- **Fixed today**: rgroup_apply.py decided whether a variant was "already
  present" by matching the first 18 chars of en-GB. Sibling wordings collide
  ("Is your spirometer close by / nearby / within reach"), so 3 of the 4
  remaining variants would have been wrongly skipped. Replaced at all 4 call
  sites (add, undo, bootstrap, post-move verify) with `en_cell_matches()`:
  exact en-GB match, or the full visible prefix when the grid truncates,
  with "?" as a wildcard for emoji the grid renders as "?". Tested offline
  against every grid cell in the fresh export: spirometry = exactly rows
  3/4 present, 4 missing; remaining mismatches are all stale-grid cells
  (the exporter bug Warden is fixing), not matcher errors.
- All rgroup_apply.py changes are uncommitted (dense-read swap,
  --restore-from mode, PMCP_WIDE, widen-order fix, en_cell_matches).

**Next (needs Raul's OK before any live write)**: run start_pmcp.sh right
before, then the same Stage3 --restore-from command, which adds the 4
missing variants. Then mail Warden to take the browser.
**Content flag for Raul**: "Is your spirometer within reach?" and "Is your
spirometer nearby?" have IDENTICAL ro-RO text ("Este spirometrul la
îndemână?"), so Romanian users would see the same wording twice in the pool.

## 2026-09-24 ~13:40 — Stage3 PARTIALLY written, live state unverified

Monitoring was already inactive for ALEX. First run: 0 writes (menubar
overflow). Fixed a real bug in rgroup_apply.py: it widened the window
before switching to the Micro Dialogs tab, so the menubar stayed narrow.
It now calls ensure_micro_dialogs first, then widens and checks for no `►`.
Rerun WROTE: tagged the canonical row "Do you have your spirometer handy?"
(checked blank first) and added "Is your spirometer within reach?"
(adjacent). The rest of the run's output is contradictory: two different
wordings were both reported "present at row 3", and "nearby" was skipped as
already present at row 4 (the "within reach" row; both have identical ro-RO
text, so the duplicate check probably matches on ro-RO). One variant hit
"popup never opened". The live table state is UNVERIFIED. Nothing more gets
written until it has been read back. Raul rejected my read-only table read
and I asked him how to proceed; Warden now holds the browser (HOLD mail
260924134049). Next: a read-only check of the v02 dialog's rows (live, or
from Warden's fresh export), then propose a fix to Raul before any write.

## 2026-09-24 — Stage3 unblocked, waiting on Monitoring toggle

Warden (260924092149): session drops were plain expiry, no lock. Logged in
fresh via start_pmcp.sh (CDP :9222). Stage3 run refused safely: browser not
in a coaching Edit view. Monitoring off is a human-only step
(WORKFLOW.md), so I asked Raul in my terminal to do ALEX -> Edit ->
Monitoring off. After that I rerun the same command, then mail Warden to
hand him the browser for the fresh ALEX export.

## RESTART CATCH-UP (2026-09-23, before a planned session restart)

**Blocked on**: Warden escalated a PMCP session-drop mystery to Raul via
PushNotification (see bottom of this file, "session dropping repeatedly"
section) — waiting on his answer before any further live browser work.
Do NOT just retry logging in again without hearing back; that was the
explicit judgment call already made this session (see rationale below).

**2026-09-23 ~13:30 update**: got the auto-resume mail (RULES 4b). Still
idle on purpose - my only open next step (Stage3 live run) is waiting on
Raul's answer about the session drops, which is exactly the "genuinely
blocked" exception. Nothing else non-browser is pending.
**NOTE for Raul**: Warden's PushNotification to you about this was NOT
delivered ("mobile push disabled in /config") - so the question is
re-asked in Loom's terminal: were you logged into PMCP as `alex-dev-2`
elsewhere ~12:20? Mirror is queued behind this for the browser too.
**Docs lead (20:41)**: PMCP v6.0 docs, start-here page: "Only one coaching
admin can work on the coaching intervention at a time" + account page's
"Reset All Locks" (admin in a coaching locks it). Nothing about session
timeouts or one login per account. So another admin in the same coaching is a
documented possible cause. Mailed Warden. Still not retrying live without
Raul's answer.

**Uncommitted code changes in the working tree** (not committed, not
reverted — real, wanted changes):
`tools/rgroups-table/rgroup_apply.py` has three additions since the last
commit: (1) the `read_table_dense` swap Warden suggested (live-verified
working), (2) a new `--restore-from`/`--to-path`/`--bootstrap-text` mode
plus `tag_randomisation_group()` primitive for retagging a rebuilt
dialog's canonical row (this session's main deliverable), (3) a
`PMCP_WIDE` env var (default 12000) replacing a hardcoded 3600px window
width that was too narrow for one specific deep top-level menu item. All
three are working/tested (CSV dry-run + live for #1 and #3's effect on
Stage1_Push); don't discard them on a fresh checkout.

**Task state**: `r_PromptForSpirometry_Stage1_Push` is DONE and confirmed
live. `r_PromptForSpirometry_Stage3` is NOT done - same restore command
(see bottom of this file) is ready to go the moment the session-drop
question is resolved; nothing else needs redoing. `r_PostponeSpirometry`
needs no action (Mason confirmed intentionally retired). Full detail and
exact resume command in `context/spirometry-retag-task.md`.

## 2026-09-21 — spirometry re-tag investigation

Task from Raul's starter mail: Mason's spirometry rebuild (commit `53b0a71`,
new micro dialog `md-030` "Prompt patient to conduct daily spirometry (v02)",
10 nodes replacing the old 51-row `md-020`) dropped the `r_` group tags on
what were 3 pools. Findings so far, cross-checked against
`data/exports/coaching_alex-v01-zum-ausprobieren_20260918-103948.json` (the
latest export, newer than the commit) and `docs/ALEX_v02_redesign_spec.md`:

- **`r_PromptForSpirometry_Stage1_Push`** (3 wordings, still live untouched
  in `md-020`) — canonical row in the new dialog is `md-030#000` ("Quick
  reminder to check your lung function with spirometry today!" — exact text
  match to the existing pool's row). Untagged. Needs re-tagging.
- **`r_PromptForSpirometry_Stage3`** (6 wordings, `md-020`) — canonical row
  is `md-030#001` ("Do you have your spirometer handy?" — exact text match).
  Untagged. Needs re-tagging. Spec §3.3 step 2 explicitly says the six v01
  rewordings "can be collapsed to one — rotate wording via the existing
  localization table if variety is wanted, not via six branch copies" — i.e.
  the spec's own intent is to keep using the `r_` randomisation mechanism
  for wording variety here, just not decision-tree branches. Confirms
  re-tagging this one is the right call, not a workaround.
- **`r_PostponeSpirometry`** (4 wordings, `md-020`) — **no equivalent
  exists in `md-030`.** Spec §2.4 and §3.2 explicitly retire the whole
  "ask if they still want to be reminded" postponement sub-flow — replaced
  by the native time-out expiry + `USER INTENTION` "remind me later" intent
  mechanism, not a branch inside the dialog. This looks like an intentional
  design decision, not an accidental drop. Recommend treating these 4
  wordings as retired rather than force-fitting them onto some node. Will
  flag to Mason for confirmation since he owns the redesign spec, not
  urgent/blocking.

Blocker found: `rgroup_apply.py`'s add flow requires an *existing* row in
the target dialog already carrying the group tag (it selects that row and
Duplicates it) — it has no path for tagging a previously-untagged row from
scratch. That's the actual "right way to re-tag" question: I need to add a
new bootstrap step (new `rgroup_apply.py` mode, keeping it inside the
pipeline rather than ad hoc clicking) that sets the `Randomisation group`
field on `md-030#000` and `md-030#001` via the message editor's own
sub-editor for that field — same property-sheet pattern the existing code
already uses for the text field, just a different field. Haven't seen that
sub-editor's DOM live yet, so writing it blind is risky.

Same pattern as every other one-off pattern this tool has hardened — watch
for it recurring in every dialog Mason rebuilds from here (explicit ask in
the starter mail).

## 2026-09-23 — retag mechanism built, ready for live write

Warden confirmed browser free, gave the go-ahead. Live read-only
inspection (Cancel/Close only, no writes) confirmed the "Randomisation
group:" field's sub-editor is a single plain `<input type=text>`,
pre-filled with the current value — same shape the code already automates
for the message-text field, just one input instead of a language-tab
pair. Also confirmed live: `read_table_dense` swap works correctly
(`--undo --dry-run --limit 1` against `r_TimelessGreetings`, clean run,
owed to Warden per his mail).

Built and CSV-dry-run-verified (no browser writes yet) a new
`--restore-from`/`--to-path`/`--bootstrap-text` mode in `rgroup_apply.py`:
sources variants from the committed `rgroups_table.csv` (not the
ephemeral generated CSV, so it doesn't touch the pipeline's auto-chained
default file) for a pool that's still live at its old location, and adds
them at a new destination path; when the group doesn't exist at all in
the destination dialog yet, it locates a pre-existing untagged row by
text match and tags it first via a new `tag_randomisation_group()`
primitive, then proceeds through the existing (unmodified) add-loop
logic. Dry-run plans for both real pools check out exactly:
`r_PromptForSpirometry_Stage1_Push` (3 variants) and
`r_PromptForSpirometry_Stage3` (6 variants), both targeting
`Prompt patient to conduct daily spirometry / Prompt patient to conduct
daily spirometry (v02)`. `r_PostponeSpirometry` confirmed by Mason as
intentionally retired (spec §2.4/§3.2) — no action, no dialog-side change
needed.

Warden reviewed, found a real gap (bootstrap tagged whatever row matched
`--bootstrap-text` without checking it was actually blank first - could
have silently overwritten a real tag on a bad match). Fixed: added a
blank-field check before calling `tag_randomisation_group`, refuses and
reports instead of overwriting.

**`r_PromptForSpirometry_Stage1_Push`: DONE, confirmed live.** `md-030`
rows 0-2 all carry the tag, adjacent, correct text. (The run's own
summary showed "errors=1" from a transient nav hiccup on the canonical
variant's turn, but the bootstrap fired correctly on a later variant's
turn and the end state is fully correct - verified directly by reading
the live table afterward.)

**`r_PromptForSpirometry_Stage3`: blocked, not done.** Hit a real width
bug along the way (fixed: `rgroup_apply.py` was resizing to a hardcoded
3600px; "Prompt patient to conduct daily spirometry" sits deep enough in
the ~107-item top-level menu that its popup wouldn't reliably open at
that width - bumped to a `PMCP_WIDE` env var, default 12000, matching
`export_coaching.py`'s own proven convention for the exact same class of
issue). But after that fix, hit a separate, more concerning pattern: the
PMCP session (account `alex-dev-2`) keeps dropping to the login screen
within seconds of a successful navigation, repeatedly, across 3 re-logins
- much faster than the documented ~1-2h silent expiry, and inconsistent
with only one CDP tab being open. Mailed Warden (260923122741) asking
whether anything else might be logging into the same account
concurrently (PMCP may be single-session-per-account) rather than keep
cycling logins on a shared resource. Holding off on further live attempts
until he responds.
