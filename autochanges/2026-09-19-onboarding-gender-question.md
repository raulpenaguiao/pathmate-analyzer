# Onboarding: new gender question for RO grammar agreement

2026-09-19. Added a new self-report question to the "🤝 Welcome" onboarding
dialog, directly motivated by the "Masculine Defaults in Romanian" audit
(63 flagged sentences defaulting to masculine grammatical forms) — its
recommended remedy #3 was "branch on the patient's stored gender, if the
platform captures one." It didn't; this adds it.

## What was built

- New **global** variable `$participantGender`, default `-99` (unset —
  matching the sentinel convention already used elsewhere in this
  coaching, e.g. medication's no-reply sentinels).
- New message in "🤝 Welcome", positioned right after the existing
  "Greet user" message (`Hello $participantName! Nice to meet you...`)
  and before the bedtime question — early enough in onboarding to inform
  everything that follows, immediately after the name is collected.
  - en-GB: "What is your gender?"
  - ro-RO: "Care este genul tău?"
  - Answer type: select one
  - Options: `Male:0` / `Female:1` / `Prefer not to say:-99` (en-GB),
    `Masculin:0` / `Feminin:1` / `Prefer să nu spun:-99` (ro-RO) — the
    "prefer not to say" sentinel matches the variable's own default, so
    declining falls straight back to today's existing masculine-default
    behavior with no special-casing needed downstream.
  - Store message reply to variable: `$participantGender`.

## A real mechanic learned along the way

The "Store message reply to variable" field is not a plain text input —
its "Edit variable:" popup has a **LOCAL / GLOBAL toggle** button, defaulting
to LOCAL. In LOCAL mode, whatever name you type gets silently prefixed
with the current dialog's own Variable Prefix (here, `$myOnboarding_`),
regardless of whether you type a bare name or one already starting with
`$`. First attempt at this field produced `$myOnboarding_participantGender`
silently instead of the intended global `$participantGender` — caught by
reading the field's displayed value back before closing, not assumed.
Fixed by clicking the toggle to GLOBAL mode before typing the name.
Confirmed no stray local variable was actually persisted server-side from
the first attempt (checked directly in the Variables tab) — the mistaken
name only ever existed inside the still-open, not-yet-saved outer message
form, never committed.

## Navigation note

"New Message" does not append inline into a visibly-editable blank row —
it immediately opens a "Create micro dialog message:" modal, and the row
only appears in the table once that modal's Close (save) is clicked. The
Welcome dialog is far larger than a naive `.v-table-body tr` count
suggests (a full scroll-and-accumulate sweep found **104** real rows, most
never rendered at once) — the new message landed at the true end (index
103) and needed **73** "Move Up" clicks to reach its intended position
(index 30). The row scrolls out of the rendered virtualized window
partway through such a long move sequence, so a click-count loop (trusting
each successful click to move exactly one position) was used instead of
re-checking visual selection after every step — confirmed correct
afterward via a fresh full sweep, not assumed from the click return values
alone.

## Still open

Nothing yet reads `$participantGender` to actually branch any of the 45
flagged masculine-default sentences — this only adds the capture step.
Branching the existing Romanian content on it is a separate, larger task
(63 sentences across 13 topic clusters, per the "Masculine Defaults in
Romanian" audit) not attempted here.
