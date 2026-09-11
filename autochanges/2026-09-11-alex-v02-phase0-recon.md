# 2026-09-11 — ALEX v02 redesign, Phase 0 recon (message timeout field + dialog delete UI)

**Coaching:** "ALEX v01 zum Ausprobieren" (sandbox — not production, per the
user).
**Driving:** the user started `tools/start_pmcp.sh`, logged in, and navigated
to the coaching (Edit, Monitoring already inactive). Claude drove everything
from there over the same CDP connection.
**Goal:** Phase 0 of `TASKS.md`'s "ALEX v02 redesign" section / the spec's
open item #6 — find the live UI for a message's expiry/timeout behaviour, and
for deleting a whole micro dialog (needed for Phase 2's prune list).

## What was navigated

1. Confirmed Monitoring state read-only (`Basic Settings and Modules` tab
   text) — already inactive, no click needed.
2. Micro Dialogs tab → widened window (~12000px) → `Prompt patient to
   conduct daily spirometry` (top-level dialog, not a subfolder) → row 4
   (`Sent as push notification`, a real reminder message, not a decision
   point) → node toolbar **Edit** → "Edit micro dialog message:" modal.
3. Clicked **"Show additional settings"** inside that modal (a collapsed
   section, not a `.v-button` — a plain expandable label) to reveal every
   hidden field.
4. Selected `Testing of gamification concept` (a P4 dev dialog already
   marked for deletion in the spec) to read the dialog-level toolbar's
   button captions. Did not click any of them.
5. Attempted to open the "Answer type" field's own sub-editor via its
   row-level "Edit" button — failed (element not enabled after the
   additional-settings expand shifted the DOM; see Tooling section). Left
   for a future pass, not blocking.

## Writes

None. Every modal opened was dismissed via **Cancel/Close**, never
OK/Save/Apply — see `probe_node_editor.py`'s and this session's new
`probe_answer_type.py`'s `cancel_top_modal`/`close_windows` helpers, both of
which only ever press Cancel/Close/Exit. Verified `document
.querySelectorAll('.v-window').length === 0` after the session. Window size
restored to 1400×1000.

## Findings

### 1. The message-level "expiry" field (spec §6, now resolved)

There is **no separate "time-out question" message *type*.** Instead, every
"Edit micro dialog message:" modal has a collapsed **"Show additional
settings"** section (click the label, not a button) that reveals, among
other checkboxes:

- **`Minutes after sending until message is handled as unanswered:`** — a
  number field with quick-pick buttons `1 / 5 / 10 / 30 / 60 / infinite`.
  This is the real expiry duration. On the spirometry push-notification
  message probed, its current value was **"0 days, 4 hours, 0 minutes"**
  (240 min) — **this is a per-MESSAGE field, distinct from the per-RULE
  "Minutes … not answered" timeout** captured in Stage 3
  (`rules_stage3_ALEX_v01.json`). v01 happens to use the same 4h default on
  both layers for this message, which is easy to misread as one field — it
  is two independent settings that should probably both be considered when
  redesigning a reminder's window.
- **`This message blocks the micro dialog until answered/unanswered`** —
  this is literally PMCP's "blocking question" the spec describes. Leaving
  it **unchecked** plus a finite unanswered-timeout is the closest thing to
  the spec's "time-out question."
- **`This message deactivates and remembers all former open questions`**
  and **`This message recalls former deactivated questions from last
  deactivation`** / **`…from most recent still filled deactivation`** — this
  *is* the "Reactivating Questions" pattern the spec names as the pile-up
  root cause (`$participantDeactivatedOpenQuestions`). v02 should leave
  these unchecked on every reminder.
- **`This message clears the current dialog cascade (and remembered
  questions)`** / **`…clears all dialog cascades…`** / **`…will not be
  cleared on clear all`** — likely the "delete, don't reactivate" lever:
  clearing the cascade instead of deactivating-and-remembering is probably
  the mechanism for "delete not reactivate," though this wasn't confirmed by
  toggling it (read-only session) — flag for a follow-up probe before Phase
  3 implementation.
- Other checkboxes seen: `This message's answer can be cancelled (NO value
  will be set on cancel)`, `This message is sticky in the client`, `This
  message is ONLY a push notification and NOT appears in the chat`, `This
  message is ALWAYS announced by a push notification`, and a `Channel to use
  for message sending:` selector.
- **No native "fallback message on expiry" field was found** on the message
  editor. The spec assumed PMCP closes a time-out question "with a short
  built-in fallback message" — not seen live. Expiry-triggered follow-up
  messaging in v01 is handled by separate decision-point/rule logic
  reacting to the unanswered state, not a built-in field. Treat spec §3.3
  step 1's "time-out fallback message" as something to build explicitly
  (a follow-up rule/message), not configure on the message itself, unless a
  later probe finds otherwise.

Full field dump (outer modal before/after expanding, all visible text):
`tools/coaching-bundle-export/spike/answertype_00_outer_before_expand_row4.json`,
`…/answertype_01_outer_expanded_row4.json`.

### 2. Whole-dialog delete UI (Phase 2 prerequisite, resolved)

Selecting a top-level dialog in the Micro Dialogs menubar exposes **two
separate toolbars**, easy to conflate:

- **Node-level toolbar** (acts on the selected row inside the dialog's
  table): `New Message`, `New Decision Point`, `New Event`, `Edit`,
  `Duplicate`, `Move Up`, `Move Down`, `Delete`. This is what
  `rgroup_apply.py` already uses.
- **Dialog-level toolbar** (acts on the whole dialog, not yet exercised by
  any tool in this repo): `New Dialog`, `Rename Dialog`, `Duplicate
  Dialog`, `Move Dialog Before`, `Move Dialog Into`, `Move Dialog After`,
  **`Delete Dialog`**. This is the button Phase 2 needs to prune the 3
  pile-up-mechanism dialogs and the 17 P4 dev/test dialogs. Not yet tested
  for a confirm-popup step (by analogy with the node-level `Delete`, which
  `rgroup_apply.py` found does show a native "are you sure?" confirm) — the
  first real Phase-2 write should confirm this on one throwaway P4 dialog
  before scripting a batch.

## Follow-up: are the "clears dialog cascade" checkboxes actually editable?

Tried, inconclusive. The outer "Edit micro dialog message:" window renders
the whole behavior-checkbox block (`deactivates and remembers…`, `blocks the
micro dialog…`, `clears the current dialog cascade…`, etc.) `disabled=true`
on every checkbox. Assumed these live behind one of the ~8 per-field "Edit"
buttons in that window (the pattern that works for Comment/text/media/
message-key/randomisation-group/store-variable fields) — specifically the
one appearing just before the "Answer options" label. **Ruled out:** that
button opens **"Edit randomisation group:"**, not a behavior/checkbox
editor — there is no separate "Edit" button for this block at all. Two
checkboxes in the block are NOT disabled (`This message is a command…` and,
inconsistently, sometimes `expects to be answered…`), which hints the block
might unlock via toggling one of those two directly rather than through a
group "Edit" button — Vaadin 7/8 "immediate" checkboxes fire a server round
trip on click even before the form is saved, so testing this blind over CDP
risks an ambiguous half-committed state. **Left unresolved** — recommend a
human clicking through it directly in the browser (faster to eye-verify,
lower-risk) rather than more scripted guessing, before Phase 3 relies on
whichever checkbox turns out to be the "delete not reactivate" lever.

## Tooling — new file

`tools/coaching-bundle-export/probe_answer_type.py` — read-only, same
Cancel/Close-only discipline as `probe_node_editor.py`. Also patched
`probe_node_editor.py` to call `_menu_nav.ensure_micro_dialogs()` before its
target loop (it previously assumed the Micro Dialogs menubar was already on
screen and failed outright otherwise).

## Session hygiene notes

- `page.screenshot()` **timed out waiting for web fonts** at the ~12000px
  probe width used for the Micro Dialogs menubar (`Page.screenshot: Timeout
  30000ms exceeded … waiting for fonts to load`). Not fatal — the script
  continued — but don't rely on a screenshot succeeding at that width;
  narrow back to a normal width first, or catch the timeout (as
  `probe_node_editor.py` and `probe_answer_type.py` already do).
- Matching a field's "Edit" sub-button by vertical proximity to its label
  (`click_button_near_label`'s nearest-`dy` heuristic in
  `probe_answer_type.py`) is fragile across a DOM reflow — it worked for
  locating the additional-settings fields' *presence* but failed to click
  the "Answer type" row's Edit button right after expanding the section
  (element briefly not-enabled, likely mid-reflow). Add a short settle wait
  after expanding "Show additional settings" before clicking anything
  inside it, or re-query the button fresh right before the click rather
  than reusing an earlier handle.
