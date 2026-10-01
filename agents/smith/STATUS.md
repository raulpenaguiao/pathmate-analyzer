# Smith — status

## ▶ Summary (2026-10-01 08:15)

**Committed today (Kart's go):** the 09-29 Chat-tab work from Raul's demo feedback:
- long variable names stack above their input
- typed-answer input (free text / numbers / date / time, to Mirror's
  `pending.input`)
- the source-coaching label (alex-live / alex-sandbox / sandbox chip + Statistics row)
- the "Engine assumptions" panel (A2 `same_pass_visibility`)

**Waiting on Raul:**
- **Advisor account** on the deployed portal: proposal mailed to Kart 09-30
  (users.json with hashed passwords, the .env user as admin, a Users page, SameSite
  cookies). Needs (a) the deployed URL and (b) advisor rights: full or
  read-only. No code until he OKs it.
- The demo tunnel (trycloudflare) has died; the local :8010 is still up. Relaunch on request.

**In progress:** r_ tool screenshots for Herald (alex-live 0930-143134
export; step 3 shows Loom's existing generated CSV, no API call).

Mail listener: `agents/waitmail.sh smith` in the background (Raul 10-01).

## ▶ Summary for Raul (2026-09-25 08:10), last 24h + open problems

**Done (committed 604855d, 7 files in `app/`, +205/−19, tests OK):**
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
1. ~~Commit?~~ **Done 09-25** per Kart's relay: 604855d (app/) + 58b7bb9 (agents/smith/). Kart pushes.
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

**09-25 ~10:30: demo portal for Raul** (Kart's relay): http://localhost:8010,
login `raul` / `chat-demo`, throwaway DATA_DIR in my scratchpad, running as
my background task. The 0925-093313 export + Report are attached unpatched.
Medication Yes/No and ACQ walks re-verified there, 0 errors.
**09-29 10:40: demo portal relaunched + public** (Mirror's relay of Raul's
ask): :8010, throwaway scratchpad DATA_DIR, 0925-093313 Report + json attached,
login raul / chat-demo (Raul confirmed it works; next time use the repo .env
login instead, his call), no LLM API key in its env. Exposed via Cloudflare quick
tunnel (user-local `~/.local/bin/cloudflared`):
https://mailman-visitors-query-lee.trycloudflare.com. Unauthenticated pages
redirect to /login (checked). Both are my background tasks, so they die with
this session. **Close the tunnel when Raul is done.**

**09-29 ~10:55, Raul's feedback from the demo (uncommitted, tests OK):**
- Variables inspector: long names overflowed under the inputs (`.var` has
  nowrap). Now the name is stacked above a full-width input and wraps anywhere,
  with a hover title. 368 rows at 1400/390px, 0 overflow. Live on the demo.
- Free-text answers ("How may I call you?", answerType `free text raw`,
  template `Please call me _`): the engine ignores `answer_type` and makes
  buttons. Diagnosis + contract mailed to Mirror (`pending.input {kind,
  multiline, template, min, max}`). **UI side done**: a typed input with the
  template around it, date -> dd.mm.yyyy. Verified with an injected
  `pending.input` (stores `Raul`, coach says "Hello Raul!"). Waiting on
  Mirror's engine side.
- Multilingual var values (`$nameOfWeek1Incentive` = "en-GB: … / ro-RO: …")
  are inserted whole. Engine fix asked of Mirror. `$weekdays` is truncated
  with "..." in the export -> Warden.
- **~11:30: Mirror's dbfc05d landed (engine side of both). Demo server
  restarted** (it doesn't reload code; same data, same login). Verified a new
  chat through the public URL: Welcome → "Please call me [__] Send" → the bubble
  reads "Please call me Raul" → "Hello Raul!". `$nameOfWeek1Incentive` renders
  per language (en/ro checked in the engine). 103 tests OK. My UI changes
  (`coaching_sim.js`, `style.css`) are still uncommitted.
- **~11:50, "One Puff → two time prompts":** the coaching logic is correct
  (node 39 first-dose, then the unconditional node 48 spirometry). Both
  questions' text is **empty in every export**. Formatted messages only have a
  `Text (html):` Report row, and the parser/enrich copy only `Text (plain):`.
  Handed to **Warden** (his area, Raul's call; I reverted my parser patch and
  mailed it as a suggestion). Next: re-attach a fixed export to the demo and
  re-walk Welcome.
- ~11:55: Warden put the HTML-text fallback in `enrich_bundle.py`; it goes into
  the new export he's finishing. The mailbox listener is armed (Monitor) and part of
  my wake-up sequence (`context/README.md`, also in `wake_prompt.txt`).
- **~13:00: Welcome re-walk passes on the newest export** (`20260929-111706`,
  which Warden re-enriched in place at 12:28, coherence ok, 0 text-less
  messages). It's added to the demo as a 2nd coaching "ALEX v01 (export
  0929-111706, newest)"; the old one is kept. Via the public URL: puffs question
  shown → One Puff → first-dose time question WITH text → spirometry time
  question WITH text → incentive question. 0 errors.
- **~13:40: source-coaching label (per Warden's 'PMCP coachings' mail).** An
  attached coaching.json now shows which PMCP coaching it came from:
  a chip by the title and in the /coachings list (`alex-live · LIVE` in
  warn colour; `alex-sandbox`/`sandbox` neutral), plus a "PMCP coaching" row in
  Statistics. Exact-name lookup (`storage.PMCP_COACHINGS`, never by prefix).
  Older bundles get the name backfilled from their stored json on first load.
  4 new tests, 111 OK. Not on the demo yet (it needs a restart, which logs Raul
  out).
- **~14:00: Chat tab "Engine assumptions" panel** (Mirror's cfa2c7e): a
  collapsible block under the controls, labelled "unverified PMCP behaviour",
  with one generic `data-setting` checkbox per assumption. First entry: A2
  `same_pass_visibility` (default on). Verified on throwaway :8011 (stopped):
  default on, unchecking persists `false` and survives reload, 0 errors.
  A1/A3 are one HTML line each when Mirror adds them.
- **Uncommitted (app/, mine):** coaching_sim.js, style.css (var names, typed
  input), storage.py, __init__.py, coaching_view.html, coachings.html,
  tests/test_pmcp_coaching_label.py.

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
