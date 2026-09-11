# 2026-09-11 — ALEX v02 redesign, Phase 3: `$currentDaySlot` rule built

**Coaching:** "ALEX v01 zum Ausprobieren" (sandbox — not production, per the
user).
**Driving:** Claude, over the user's CDP session (continuation of the same
session as Phase 3's variable creation).
**Goal:** the first unchecked Phase 3 sub-item in `TASKS.md` — a new
PERIODIC BASIS rule that computes `$currentDaySlot` from `$systemHourOfDay`
against the 3 hyperparameters created earlier this session (spec §2.3).

## Where the rule lives

PERIODIC BASIS's tree has two top-level branches under
`Execution on PERIODIC BASIS`: `🚀 Only perform if daily rules have NOT been
already performed` and `🚀 Only perform if daily rules have been already
performed`. The second is the normal-operation branch — every real periodic
feature check (spirometry postponement check, sensor-data poll, the
`$userRequestedNewTime...` reschedule checks, etc.) lives nested under it as
a depth-2 sibling. The 4 new day-slot rules were added there, as 4 more
depth-2 siblings, appended after the existing ones.

## Rule design actually used (cascading overwrite, not nested elif)

A single rule row cannot both compare two values AND store an unrelated
literal — the "Store rule result to variable" target always receives either
the comparison's boolean result or Rule[x]'s own computed value (operator-
dependent), never a third, independent literal. Confirmed by precedent
already in the coaching: `r-089` ("Check whether
$userRequestedNewTimeForEducationalContents=1") is a real-comparison gate
with **one nested child** (`r-090`, an unconditional "always true" reset)
that only runs if the gate is true. Children of a condition-rule tree node
only execute when that node's own condition evaluates true — this is how
"if/then" is expressed in this rule tree; there is no native `else`.

Building a full elif-ladder (4 levels of nesting, using inverted guards for
"not yet matched") was considered and rejected as needlessly deep. Instead,
since the day-slot buckets are ordered by a single ascending threshold, a
flatter **cascading overwrite** works and only needs one level of nesting per
bucket:

```
(depth 2) Gate: $systemHourOfDay < $hyperparameterEveningEndHour
  (depth 3) → $currentDaySlot = "evening"          [widest bucket, runs first]
(depth 2) Gate: $systemHourOfDay < $hyperparameterMiddayEndHour
  (depth 3) → $currentDaySlot = "midday"
(depth 2) Gate: $systemHourOfDay < $hyperparameterMorningEndHour
  (depth 3) → $currentDaySlot = "morning"           [narrowest, runs last —
                                                       wins for morning hours]
(depth 2) Gate: $systemHourOfDay >= $hyperparameterEveningEndHour
  (depth 3) → $currentDaySlot = "night"             [disjoint from the above,
                                                       order doesn't matter]
```

All 4 top-level gates are **siblings** (all children of the same
"...already performed" branch), evaluated top-to-bottom every tick. Because
`morningEnd < middayEnd < eveningEnd`, a morning hour makes all three
`< X` gates true; they fire in the tree's creation order (evening→midday→
morning), each unconditionally overwriting `$currentDaySlot`, so the
**last, narrowest match wins** and the final value is always correct. No
compound/AND expression was needed and no deep nesting was needed — this is
the cheaper equivalent of an elif-ladder given monotonic thresholds. Each
gate's condition operator is `calculated value is smaller than` (buckets
1–3) or `calculated value is bigger or equal than` (bucket 4, night); each
child uses `create text but result is always true`, storing the literal
bucket name to `$currentDaySlot`.

Live tree captions (final, confirmed clean):
```
🚀 Only perform if daily rules have been already performed
  ...(15 pre-existing feature rules, unchanged)...
  Day-slot gate: hour < eveningEndHour (ALEX v02 spec 2.3): $systemHourOfDay calculated value is smaller than $hyperparameterEveningEndHour
    evening (ALEX v02 spec 2.3): evening create text but result is always true → $currentDaySlot
  Day-slot gate: hour < middayEndHour (ALEX v02 spec 2.3): $systemHourOfDay calculated value is smaller than $hyperparameterMiddayEndHour
    midday (ALEX v02 spec 2.3): midday create text but result is always true → $currentDaySlot
  Day-slot gate: hour < morningEndHour (ALEX v02 spec 2.3): $systemHourOfDay calculated value is smaller than $hyperparameterMorningEndHour
    morning (ALEX v02 spec 2.3): morning create text but result is always true → $currentDaySlot
  Day-slot gate: hour >= eveningEndHour, i.e. night (ALEX v02 spec 2.3): $systemHourOfDay calculated value is bigger or equal than $hyperparameterEveningEndHour
    night (ALEX v02 spec 2.3): night create text but result is always true → $currentDaySlot
```

## New Rules-tab write mechanics found this session (important for Phase 3's remaining rules)

### The Rules tree's "New" toolbar button is unreliable for nesting — use Duplicate instead

Phase 1 never needed to create a *new* rule (only edit existing ones), so this
wasn't discovered until now. Selecting an existing tree node and clicking
**New** is *supposed* to create the new rule as a **child** of the selected
node (confirmed working once, on a genuine never-touched leaf). But across
~8 attempts this session, it **silently created the new rule as a stray
5th top-level section** (a sibling of `Execution on DAILY BASIS` etc.)
roughly half the time, with no visible error — the only way to catch it is
to commit, re-dump the tree, and check the new node's `depth`. Root cause
not identified (not correlated with parent-expanded-state, wait time before
the click, or anything else tried). **Every stray top-level rule created
this way was caught and deleted before it could pollute the coaching** — see
the repeated "delete stray, retry" cycles in this session's tool-call log.

**Working, reliable alternative for adding a new SIBLING at a known depth**:
select an *existing* rule at that depth, click **Duplicate** (no confirm
popup, no modal — it's instant), which reliably creates an exact copy as a
sibling immediately after the source, then open that copy's Edit modal and
overwrite its fields. Used for all 4 gate rules here (duplicated `Save
current time in decimal format`, a depth-2 leaf under the same parent, 4
times). 100% reliable across this session, 0 misplacements.

**New still had to be used once per gate**, to add each gate's own nested
child (no existing depth-3 rule to duplicate from a fresh gate). Reliability
there improved (but was not 100%) with a **longer wait after selecting the
parent before clicking New** (~1000ms, vs the 400-600ms used elsewhere in
this codebase) — 3 of 4 nesting attempts succeeded on the first try with
this longer wait; the 4th (night's child) still landed as a stray top-level
node on the first attempt and needed one delete-and-retry. **Always verify
placement by depth after committing, every single time** — do not trust that
a `New` click nested correctly just because a "Create rule:" form appeared
and accepted input.

### Duplicating a rule copies its "Store rule result to variable" field — clear it explicitly

The duplicated source (`Save current time in decimal format`) stores to
`$timeDecimal`. Editing Comment/Rule[x]/operator/Term[y] does **not** touch
`storeResultVariable` — it silently carried over into all 4 gate rules, so
every time a gate's own comparison evaluated true, it would have overwritten
the **real, pre-existing** `$timeDecimal` variable (used elsewhere in the
coaching) with the gate's own boolean 0/1. **Caught before this ever went
live** via a final sweep of all 8 new nodes' captions (which include the
store-target in the `→ $variable` suffix) — 4 gates all showed
`→ $timeDecimal`, which should never have been there for a pure gate.
Fixed via the "Edit variable:" popup (field #3): its text input holds the
current store-target; clearing it (`fill("")`) and clicking OK resets the
field to "(no value set)", confirmed via the popup's own live re-render
before closing. **Lesson for any future Duplicate-then-edit rule build**:
always explicitly check (and clear, if not wanted) `storeResultVariable`
after duplicating — it is not part of the "obvious" fields you'd think to
edit (comment/condition/checkboxes) and duplicating specifically to reuse a
*calculation* rule (as opposed to a plain gate) makes this an easy miss.

## Session hygiene notes (reconfirmed)

- The "Edit button not enabled" / "Delete button not enabled" intermittent
  Vaadin quirk (documented in the Phase 1 completion log) recurred
  repeatedly here too, on both `open_rule_modal` and the Delete flow —
  always resolved by simply re-running the same call a few seconds later,
  never needed a different approach.
- Verified end of session: `open modals: 0`, exactly 8 tree nodes match
  `ALEX v02 spec 2.3` / `currentDaySlot`, no orphaned top-level stray rules
  remain (checked via a full-tree grep for both markers, not just spot
  checks).

## Next

Per `TASKS.md` Phase 3: rewrite the DAILY BASIS reset rule for spirometry
(spec §3.2), which now has `$currentDaySlot` available to clip
`$spiroWindowEnd` to "end of the next day-slot boundary" as designed.
