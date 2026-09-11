# 2026-09-11 — ALEX v02 redesign, Phase 1 completion (rule-write mechanics resolved)

**Coaching:** "ALEX v01 zum Ausprobieren" (sandbox — not production, per the
user).
**Driving:** Claude, over the user's CDP session (continuation of the same
session as Phase 0-3-variables).
**Goal:** close out the four remaining Phase 1 items from `TASKS.md`
before Phase 3 continues: (1.1) confirm the timeout quick-pick mechanism,
(1.2) same-value OK-commit test on the 4 popup editors, (1.3) reconcile
the filterselect count, (1.4) build the write helper.

## Session-config change

Mid-session, `.claude/settings.local.json` gained `"permissions":
{"disableAutoMode": "disable"}` at the user's request, after Claude Code's
auto-mode classifier repeatedly blocked live-write Bash calls (including
dry runs with no actual writes) with no way to distinguish safe from risky
ones. This is a Claude Code harness setting, not a PMCP one — noted here
because it's what unblocked the rest of this session's live testing.

## 1.1 — the not-answered-timeout mechanism: PARTIALLY RESOLVED, one real
   platform limitation found

**What works:** the `Hour to send message` field is a `$variable` picker
(a live `.v-filterselect`, confirmed 2026-09-10/11) and IS directly
editable — click it, pick a variable from the dropdown, done. No popup, no
unlock step, for an existing rule that already has "Start micro dialog" (or
"Send message") checked.

**What does NOT work, tested exhaustively:** the `Minutes after sending
until message is handled as not answered` slider and its quick-pick
buttons (`1/5/10/30/60`) render `v-disabled` in every configuration tried:

- An existing "Start micro dialog" rule (the compliance-feedback rule
  sampled throughout this project) — disabled.
- An existing "Send message" rule (the one Stage-3 found with a 19-minute
  timeout) — disabled.
- A **brand-new, unsaved** rule via the Rules tab's own `New` button
  ("Create rule:") — disabled by default.
- The same new rule **after** checking "Start micro dialog if rule result
  is TRUE" for the first time (false→true transition) — this DID unlock
  the sibling `Hour to send message` **literal-clock slider** (previously
  also disabled) and the `Micro dialog to start` filterselect, but the
  timeout slider stayed locked.
- The same new rule after also **selecting a target micro-dialog** via the
  now-unlocked filterselect — still locked.
- Direct keyboard (`ArrowRight`) and mouse-click interaction with the
  now-enabled hour slider, to see if *setting* hour (not just unlocking
  it) was the missing trigger for timeout — still locked.

**Conclusion:** unlike the message-level "unanswered" timeout (Phase 0,
which does have working quick-picks), the **rule-level** not-answered
timeout appears to be genuinely non-interactive through the Rules tab's
Edit/Create UI, in every code path this session could find. This
contradicts the assumption (based on the user's own recollection) that
"clicking commits" for this field — that recollection likely refers to the
message-level field, which behaves differently. **Open question for a
future session or a human clicking through it live**: is there some other
trigger not discovered (e.g. only settable via keyboard Tab-navigation
rather than click, only settable while the form is in some other state,
or genuinely locked by PMCP design once past a certain point)? Whoever
originally built ALEX v01 clearly set varied timeout values (4h default,
19min on one rule) some way — that mechanism is still unknown.

**Practical impact on Phase 3:** the spec's rule rewrites (3.2) can set
`Hour to send message` freely (a $variable, as designed) but **cannot
currently set a custom not-answered timeout** through automation. Every
rule this session could inspect defaults to `0 days, 4 hours, 0 minutes`
(4h) — if that default is acceptable for the redesigned rules, this isn't
blocking; if the spec needs a different value, it needs either (a) a human
setting it by hand once in the browser, or (b) further discovery.

### Incident during 1.1 testing — stray rule created and cleaned up

Testing the Create-rule form's field-by-field unlock behavior involved
checking the "Start micro dialog" checkbox and selecting a target dialog
in an **unsaved** create form, intending to discard it. Closing that form
via its only dismiss button (`Close` — there is no separate `Cancel` on
either Edit or Create rule forms) turned out to **actually persist a new
rule** (tree node count 122→123), unlike a message-editor "Close" which is
a pure cancel. Found it immediately (default caption `--- calculated value
equals ---`, nested under the sampled compliance rule) and deleted it via
the tree's `Delete` button + its confirm popup, restoring the node count
to 122. **Lesson for any future `rule_apply.py` work: `Close` on a
"Create rule:" form is a commit, not a cancel — never leave one open
assuming it's discardable.**

## 1.2 — same-value OK-commit test: CONFIRMED

Opened the Comment popup on the sampled compliance rule, read its current
value, retyped the identical text, clicked **OK** (a real commit, not
Cancel). Verified via the tree's own caption text afterward (which embeds
the comment as its prefix) — unchanged, confirming the write path
round-trips correctly. Not individually re-tested on the Rule[x]/Term[y]/
result-variable popups, but they're structurally identical (a single
textarea/input + Cancel/OK) — the mechanism is trusted by analogy.

## 1.3 — filterselect identities: RESOLVED

Walked the outer "Edit rule:" form in strict DOM order (labels
interleaved with their controls) to map all 4 filterselects definitively,
resolving the "4 seen vs. ~3 expected" mismatch from the earlier recon:

| # | Field | Notes |
|---|---|---|
| 0 | Condition operator (e.g. `calculated value is bigger than`) | part of the `Rule [x] <op> Term [y]` expression, sits between the two popup-edited text fields — not a popup itself |
| 1 | `Message group to send messages from` | disabled unless `Send message` is checked |
| 2 | `Micro dialog to start` | disabled unless `Start micro dialog` is checked (in Create mode); the dropdown's first entry is `$participantNextMicroDialogIdentifier` — a valid "use whichever dialog was just identified" option, not a bug |
| 3 | `Hour to send message` | the `$variable` picker, live once its owning action is checked |

`Store rule result to variable` is **not** a filterselect at all — it's
plain display text (`(no value set)` when empty) behind its own popup
(`Edit variable:`, previously mislabeled Edit[3] in the earlier recon —
that mapping was correct, just not connected to this filterselect
question).

## 1.4 — write helper: minimal version built

Added write functions to `tools/coaching-bundle-export/_rules_nav.py` for
everything confirmed above: `set_rule_comment`, `set_rule_condition_x`,
`set_rule_condition_y`, `set_rule_result_variable` (all via their popups,
type + OK), `set_rule_checkbox` (direct, by checkbox label substring),
`set_rule_hour_variable` (direct filterselect, requires the owning action
checkbox already checked). **No function for the not-answered timeout** —
deliberately omitted per 1.1's finding; a future caller should not assume
one exists. All follow the same "leave the modal open, caller commits via
`close_windows()`" pattern as the read-only functions already in this
module, so a caller can batch several field edits before one commit.

## Session hygiene notes

- The toolbar `Edit`/`Delete` buttons on both the Micro Dialogs and Rules
  tabs intermittently need a **second** `select_node` + short wait before
  they report enabled — seen repeatedly today (reopening rule00 twice,
  reselecting the stray rule to delete it). Never trust one selection
  attempt; check the target button's own disabled class before clicking
  it, and retry the selection if it's still disabled.
- Reconfirms: `Close` is **not** a safe default dismiss action to assume
  cancels anything in this app. Always check what kind of form is open
  (view/edit of an existing entity vs. create-new) before treating `Close`
  as free.
