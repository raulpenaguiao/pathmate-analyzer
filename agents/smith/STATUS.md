# Smith — status

## ▶ Summary for Raul (2026-09-25 08:10), last 24h + open problems

**Done (all uncommitted, 7 files in `app/`, +205/−19, tests OK):**
- **Chat tab now runs on the coaching.json engine (Stage 4 Phase E).**
  Engine-aware routes: old HTML-sim chats keep their engine and show a
  notice. Chat routes require an attached bundle. Auto-periodic toggle,
  not-answered countdown, labelled launch/timeout/suppressed events.
  Questionnaire aid for `open-component` steps.
- **Acceptance walks all pass in the browser** (with Mirror + Warden):
  medication reminder Yes and No paths, and ACQ reminder → answers →
  questionnaire → correct score → next ACQ date scheduled. Mirror has marked
  Phase E done with these as evidence.
- **Stale-chat guard (your per-export-id rule):** a chat built on a
  different export of the coaching.json is refused (except reset). Attaching
  a new bundle clears the old rgroups CSVs.
- **UI fixes from the live-browser QA pass:** Chat variable inputs were
  1 char wide. The sticky tab bar hid the tab labels at phone width.
- Along the way I found engine bugs for Mirror to fix: answer options were
  parsed backwards, decision branches weren't skipped, decision nesting
  wasn't exported. All fixed now.

**Open problems / decisions for you:**
1. **Commit?** Everything above is uncommitted, waiting on your go-ahead.
2. **Your live portal (:8000):** "ALEXv1_14th" has a stale 09-14
   coaching.json attached (no jump targets or nesting, predates the v02
   dialogs). Best replacement now: today's `..._20260925-093313.json`
   (Mirror confirms it works unpatched in the engine). Via Detach + Attach on
   the coaching's Statistics tab. It will show the mismatch banner, because it
   flags 4 wrongly-swept dialogs itself, and that's expected. I haven't
   touched your instance.
3. **Fresh export exists now** (Warden, `..._20260925-093313.json`). The
   medication options are fixed in it, **but the same one-line `Yes:1 No:0` /
   `Da:1 Nu:0` bug is live in "Prompt patient to conduct daily spirometry
   (v02)", rows 3-4 ("Do you have your spirometer handy?").** It probably
   came from the same v02 build script, and the 09-19 fix only covered the
   medication doses. On a device this sends the raw text instead of two
   buttons. Needs a live fix (Mason/Warden, mailed 09-25). The export itself
   also flags 4 dialogs read from the wrong table (Warden is on it).
4. **Step 3 of Randomisation groups (LLM generate) is still untested in a real
   browser**. It needs you and an API key.
5. **Not verified:** how `open-component` behaves on a real device. The docs
   say it blocks the chat until the questionnaire is done. The sim relies on
   the user setting `$acq_*` by hand.

Details below, newest at the bottom.

## 2026-09-23

Answered Mirror's Chat-tab coordination questions (Stage 4 engine plan,
`docs/stage4_chat_engine_plan.md` Phase E) — no code changes yet, just
design alignment ahead of her building it:

- Clock UI stays as-is (`+1 min`/`+1 hour`/`+1 day`/`next slot`/`run
  periodic`), computing `to_time` client-side for her `advance()` call.
- `set_var` stays a first-class action, driven by the existing editable
  Variables-inspector rows.
- Chat tab bundle-gating: template-level gate already exists
  (`coaching.get('bundle')`); I'll add the matching route-level
  `_require_bundle()` check (like rgroups already has) when Phase E lands.

Kart replied (260923084152): prioritize the export/coaching.json coherence
check over a visual rules/dialogs nav. **Done**, same session:

- The coherence data (`validation.ok`/`warnings` from
  `export_coaching.py`'s phase-5 check) was already computed and stored in
  `meta.bundle.summary.coherenceOk/coherenceWarnings` (`app/storage.py:127-140`)
  and already rendered — but only buried in a table on the Statistics tab
  (`coaching_view.html:93-109`), not loud.
- Added a page-level `.page-banner.is-danger` banner at the top of
  `coaching_view.html` (visible on every tab, not just Statistics) when an
  attached bundle's coherence check failed, with a "See details in
  Statistics" jump link (new `data-goto-tab` click handler in
  `coaching_tabs.js`, since it's not a real tab button).
- Added a `chip-danger` "⚠ export/JSON mismatch" badge next to the
  coaching's name in the `/coachings` list table, so drift is visible
  without opening the coaching at all.
- New `.page-banner`/`.page-banner.is-danger` CSS (mirrors the existing
  `.sim-banner`/chip pattern already in `style.css`).

Verified: full `unittest discover` suite (60 tests, all pre-existing,
untouched by this change) still passes. Wrote and ran a throwaway Flask
test-client smoke script (not committed) covering: banner+badge render on
a `coherenceOk:false` bundle, no false-positive on a `coherenceOk:true`
bundle, no false-positive on a coaching with no bundle attached at all.
Not a live-PMCP session (pure repo/template work) — no `autochanges/`
entry needed, per that folder's own README.

Changes are in the working tree, not committed (repo convention here
mirrors the global default — only commit when explicitly asked). Told
Kart it's done; will commit if/when asked.

## 2026-09-23, later

Started scoping the visual-nav idea myself (Kart left sequencing to me,
mailbox stayed quiet ~1.5h). Found a real blocker, not a quick win:
`coaching_view`'s Rules/Dialogs/Variables/Statistics tabs always render
from the HTML-parsed model (`load_model`/`parse_model`), never the
bundle-parsed one (`load_bundle_model`/`parse_bundle`), even with a
`coaching.json` attached — so bundle-only fields like
`Rule.micro_dialog_path` (which dialog a sender rule launches — not
derivable from the HTML at all, confirmed against the rule caption text)
can never show up there. Built a rule→dialog jump link, caught it
rendering nothing in a smoke test, traced the cause, **reverted** rather
than ship dead code. Switching those tabs' model source has a real
regression risk (`parse_bundle` models always have empty
`message_groups` — known Stage-3 gap) so it's not my call to make alone;
mailed Kart (260923104343) flagging it as a decision point, and gave
Mirror a heads-up (260923104350) since it overlaps the Phase E "which
model backs which view" question we'd already opened.

Not blocked — will pick a different, cleanly-scoped increment next
rather than wait on that answer.

## 2026-09-23, session-end flush (restart incoming)

Mailed Kart a scan of two candidates (patient-model auto-play; HTML-only
Rules-tab polish) asking for a concrete pick rather than risk a third
guess-and-revert. Kart replied (260923122814, read):
- Confirmed the bundle-vs-HTML question is **purely my own call, no
  rush** — Mirror confirmed Stage 4 Phase A uses a separate
  `load_bundle_model()` entry point, doesn't touch it.
- Patient-model behavioral design + workstream-5 ownership are
  genuinely unassigned; Kart flagged that for Raul, not mine to chase.
- **Concrete assigned task, fully unblocked, no sign-off needed:** a
  live-browser click-through QA pass on my own existing tabs — TASKS.md
  flags the Randomisation Groups tab (steps 1-3) as "not yet exercised
  by a human in a real browser," only Flask-test-client-smoke-tested so
  far. General click-through of all my tabs, not just that one.

**In-flight, interrupted by this restart notice, effectively not
started:** I'd just launched a throwaway portal instance to do this
(`DATA_DIR` in my scratchpad, port 8010, throwaway
`APP_USERNAME=qa`/`APP_PASSWORD`/`APP_SECRET_KEY`, `.venv/bin/python
wsgi.py`) and confirmed `/login` returned 200 — **no browser
interaction happened yet, no data uploaded, nothing to undo.** I killed
that process immediately on getting this restart notice (port 8010
confirmed clear). Planned test data (not yet used): upload
`tests/fixtures/coaching_ALEX_v01.html` as the coaching +
`data/exports/coaching_alex-v01-zum-ausprobieren_20260918-103948.json`
(matching timestamp) as its bundle, to exercise the rgroups tab with
real thin r_ pools.

**Next session should:** pick the live-browser QA pass back up from
scratch (nothing persisted from the throwaway attempt — scratchpad dir
won't survive/matter across sessions, that's fine, it's disposable). Use
the `run` skill → browser-driven pattern; no project-level run skill
existed as of this session (worth `/run-skill-generator` if this becomes
a recurring need). Remember: port 8000 is Raul's own live instance —
always use a different port + isolated `DATA_DIR` for QA, never touch
his running one or his real `data/` in place.

Working tree still only has the coherence-banner/badge change from
earlier today (uncommitted, verified, see above) — nothing else pending
in the repo. No live-PMCP/Playwright session this whole day (pure
Flask-app work), so no `autochanges/` entry applies.

Stopping now per Raul's restart notice — not starting anything new.

## 2026-09-23, afternoon (post-restart)

Restarted, inbox had Raul's behavior-change mail (auto-resume on wake;
Kart owns `git pull`) — read + archived. Per that, resuming the assigned
live-browser QA pass of my tabs (esp. Randomisation Groups) on my own:
throwaway instance, separate port + scratchpad `DATA_DIR`, never port
8000. Test data: matched pair `data/exports/Report_alex-v01-zum-ausprobieren_20260917-174650.html`
+ `coaching_alex-v01-zum-ausprobieren_20260917-174650.json` (uploaded
into the throwaway DATA_DIR only). Local Flask app only — no PMCP
browser, so no Warden check needed.

**QA pass done (headless Chromium via Playwright, throwaway :8010, stopped
after; :8000 untouched).** Uploaded matched HTML+json pair, clicked every
tab (Stats/Rules/Dialogs/Variables/Chat/Rgroups/Raw), rules filter + tree,
rule→variable jump link, new chat + clock tick, rgroups steps 1→2 (413
table rows, 100 thin pools; step-2 gated until step 1; state survives
reload; both CSV downloads 200), step 3 gating only — **no LLM call made**
(needs a real API key; empty-submit correctly blocked client-side). Zero
console/page/HTTP errors. Coherence banner/badge correctly absent
(bundle is coherent).

Two real bugs found + fixed (uncommitted, in working tree):
1. Chat Variables inspector: value inputs squeezed to ~17px — `2026`,
   `01.01.2026`, `night` showed as one char. Fix: `#sim-vars`
   fixed table layout + wrapping names (`style.css`). Verified at
   1400/800/390px: every value fits.
2. Sticky tabbar hard-coded `top: 53px`/`49px` vs real topbar height
   (49px desktop → 4px see-through gap; 73px at phone width → header hid
   24px of the tab labels). Fix: `coaching_tabs.js` measures the topbar
   into `--topbar-h` (on load + resize), CSS uses it with the old values
   as fallback. Verified gap = 0 at both widths.

Full suite: 78 tests OK. Human-in-a-real-browser step 3 (LLM generate)
still unexercised — needs Raul + an API key.

Mirror mailed (260923135403) proposing the Phase E split: engine
exposes state, I own routes/UI/gating. Agreed + sent my wanted state
fields (engine marker, pending timeout_at, structured event kinds,
auto-periodic semantics). Next: route-level bundle gating for the chat
routes (independent of Mirror's answer).

**Phase E, step 1 done (uncommitted):** route-level bundle gating in
`app/routes.py`: `_require_bundle()` on chats list/new/get/step and
`.pmcp` participant-import (rename/delete left open for cleanup after a
bundle is detached). Smoke-tested via Flask test client in an isolated
DATA_DIR: no-bundle coaching → all five 404, view still 200; bundle
coaching → all 200 (import 302 flash-redirect as before). Suite OK.

**Waiting on Mirror** for the state-field answers (esp. `state["engine"]`
marker) before switching `sim/init`/`step` to `load_bundle_model`. Doing
it without the marker would step old HTML-sim chats with the new engine.
Nothing else in flight.

**~17:15:** Still blocked on Mirror for Phase E (engine marker). She read
my 14:04 mail and didn't reply. My 16:43 nudge is still unread in her
inbox, and her STATUS hasn't changed since 15:53. Her session looks
idle/stopped. Not urgent. If Raul wants Phase E moving, waking Mirror
unblocks it. Idle meanwhile, listener armed.

## 2026-09-23, evening: Phase E Chat-tab wiring (uncommitted)

Mirror delivered all 4 engine fields (commit 4b223e5). Wired them in:
- `routes.py`: new `_chat_model()` picks the model from `state["engine"]`
  (missing/`"html"` → `load_model`, `"bundle"` → `load_bundle_model`,
  `None` import snapshot → bound to bundle on first step). New chats use
  the bundle engine. `chat_get` also returns `engine`.
- UI: notice on legacy HTML-sim chats; "auto-run periodic rules" checkbox
  (→ `set_setting`, persisted in state); pending not-answered countdown
  from `timeout_at`; labelled/coloured bubbles for launch / timeout /
  suppressed / unresolved_target events. Banner text updated.
- Deliberately **no jump links** from events to Rules/Dialogs tabs: event
  refs are bundle indices/uids, the tabs render from the HTML model, so
  anchors may not match (same trap as the earlier reverted attempt).

Verified in headless Chromium on throwaway :8010 (stopped): legacy chat
shows notice; new chat is bundle (359 seeded vars, `$currentDaySlot`
morning at 09:00); toggle off persists across reload; 6 simulated days →
only `unresolved_target` events (known broken senders), **no sender
launched** — expected until Mirror's `$participantParticipationInDays`
fix lands, so the plan's Phase E acceptance (ACQ reminder → answer →
completion in browser) can't be done yet. Countdown + all 4 event styles
verified on a seeded chat (2h15m → 1h15m after +1h). Regression
click-through clean, 78 tests OK.

Next: re-run the acceptance walk once Mirror's fix lands.

## 2026-09-24, morning: Phase E acceptance walk → 2 engine bugs (Mirror's)

Mirror's 98e19f0 fix landed (senders launch). Ran the walk through the Chat
tab UI (throwaway :8010, stopped after): set `$onboardingDone=1` + times,
8 × "+1 day", answered each question. UI side all good (launch/suppressed
events, countdown, 0 errors). Engine results wrong, reported to Mirror
(260924061003):
1. `coaching_sim.py:752` `_options()` has label/value swapped since
   f847680. PMCP docs say "Display Label:Transmitted Value". So buttons
   show "1"/"0", and answering writes "Yes" into the var, so every
   `equals 1` decision after a question fails. **Affects every sim run
   with answer options, HTML sim included.**
2. A false decision node doesn't skip its branch: both "Thanks…" and "No
   worries…" play.
Also: the 0917/0918 exports predate Raul's 09-19 live fix of the
medication `Yes:1 No:0` single-line options, so a fresh export is needed
for a clean walk. Walk re-run pending Mirror's fixes. My Phase E UI work
is still uncommitted.

**Re-walk on Mirror's 6d3719e: Yes path PASSES.** Stale 0917 export
first: single "Yes:1 No" button stores 0, and "Thanks" still plays (the No-path
gap, see below). Then applied Raul's 09-19 options fix to the **throwaway
bundle copy only** (scratchpad DATA_DIR, real data/ untouched). 3 days ×
rule #145 launch → "Yes" → "Thanks…" only. Final vars
`confirmAnswer_1=1, done_1=1, engaged_1=0` match a hand-trace of the v02
dialog's nodes exactly. 0 UI errors, 78+ tests OK.
**No path still open:** coaching.json doesn't export "jump to message if
FALSE" targets. Mirror asked Warden to add them to the export. It needs a fresh
export once that lands (would also fix the stale options). Then the final
walk (No path + ACQ flow) can be done.

**2026-09-24 ~09:30: Yes AND No paths pass** on Warden's enriched
`..._20260918-103948_jumps.json` + matching 0918 Report, uploaded through the
portal UI into a fresh throwaway DATA_DIR (stale one-line options patched
in the throwaway copy only). No: "No worries…" only, vars
confirm=0/done=0/engaged=0. Yes: "Thanks…" only, 1/1/0. Both match a
hand-trace of the "Prompt patient to take first dose of controller medication (v02)" dialog. Tests OK, :8010 stopped.
Caveats:
- The 0918 export **fails its own coherence check** (699 nodes vs baseline
  1049, down 33%). My mismatch badge flagged it on upload, as designed. Told Warden.
- Plan's acceptance names the **ACQ** reminder flow. I walked the medication
  flow. The ACQ walk should be done on a fresh, complete export (it would also
  carry the 09-19 options fix).
- Raul's live portal (:8000) has a stale 09-14 bundle attached to
  "ALEXv1_14th" (per Warden). Re-attaching is Raul's call. I haven't touched it.

**~10:30: ACQ walk** on Warden's complete `..._20260917-174650_jumps.json`
(coherence ok, no badge; options patched in throwaway copy). r-098 launches
the "Prompt patient to answer questions of the ACQ" dialog at the set day/hour, answers Yes/Go! work. **Completion can't be
judged yet.** Node 25 `open-component:…` is undocumented in the PMCP docs (it
presumably opens the in-app ACQ, which writes results externally). Also
two engine oddities (`$userRequestedNewTimeForACQ` set to 1 unexpectedly;
r-124 fires with send-hour var -99). All sent to Mirror (engine-side).
Medication Yes/No walks: done. Phase E UI work: done, still uncommitted.

**~11:15: questionnaire UI aid added (uncommitted)** after Mirror's
59e80ec (open-component → one "Start questionnaire" option with
`component`/`questionnaire_id`). The pending area now shows a note ("opens
questionnaire acq-0 in the app, answers aren't exported, set the vars
first") plus a "Show $acq* variables" button that filters the inspector.
Browser-verified: ACQ walk reaches it, set `$acq_completed=1` +
`$acq_q1..6`, "Start questionnaire" → dialog completes, acq_completed=1.
Remaining wrongness is Mirror's Q2 export gap (decision-rule nesting not
exported): `$acq_q7` stays -99 (FEV1=80 should give 2), so the score is
-13.29. Real var edits post set_var once (verified). Tests OK, :8010 stopped.

## 2026-09-24, late morning: ACQ passes; stale-chat guard (uncommitted)

**ACQ flow passes end to end** on Warden's depth-enriched 0917 `_jumps.json`
(Mirror's 2749c6f nesting fix). Reminder → Yes/Go! → questionnaire
(vars set via the new aid) → `$acq_q7=2`, `$acq_score=1.1429`,
`$userRequestedNewTimeForACQ=0` (matches Mirror's hand-check). Next daily
run advances `$dateOfNextACQ` 03.01 → 04.01 via r-012
(`$hyperparameterNumberOfDaysBetweenACQs=1` in this sandbox). **The Phase E
acceptance walks (medication Yes/No + ACQ) are all done.**

**Stale-chat guard, per Raul's rule** that md-/node/rule uids are
per-export positions (Warden 260924092522): saved chats hold positional
refs, so a chat must not be continued against a re-exported bundle.
- `routes.py` `_fingerprint_status()` compares the chat's
  `state["model_fingerprint"]` (Mirror's 17e1e6e) with the attached bundle's.
  "stale" → step refused (409) except `reset`. "unknown" (no key) →
  warning only.
- Chat tab: red "built on a different export" notice / grey "predates
  fingerprints" notice. A refused step leaves the state untouched.
- `storage.save_coaching_bundle`: attaching over an existing bundle now
  clears the rgroups CSVs (they carry `nodeUid`s).
- Verified: test-client matrix (same file re-attached → ok; different
  export → stale + 409; reset → ok; no key → unknown; CSVs cleared) +
  browser swap via Detach/Attach. Tests OK, :8010 stopped.
