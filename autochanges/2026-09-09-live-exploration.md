# 2026-09-09 — live PMCP exploration (Stage-3 discovery)

**Coaching:** "ALEX v01 zum Ausprobieren" (sandbox — not production, per the
user).
**Driving:** both. The user logged in and clicked anything that changed live
state on request (Monitoring toggle); Claude drove navigation and read-only
probing over CDP (`http://127.0.0.1:9222`, a Chromium the user started with
`--remote-debugging-port=9222`).
**Goal:** figure out what fields actually exist for message send-delay,
priority, and answer routing, ahead of building Stage 3 of the coaching
exporter.

## What was navigated

1. Coachings → "ALEX v01 zum Ausprobieren" → Edit → Basic Settings and
   Modules → Monitoring toggle (see Writes below) → Micro Dialogs.
2. Micro Dialogs → widened window to 12000px → "👋 Hello / Morning
   greetings" dialog → row 0 and row 1 → each row's "Edit micro dialog
   message:" modal, read via `tools/coaching-bundle-export/probe_node_editor.py`.
3. Rules tab → "Execution on PERIODIC BASIS" → expanded → selected the leaf
   rule "If still in time, send repeated reminder for spirometry
   measurement" → its "Edit rule:" modal.
4. Units tab (quick look — turned out to be a topic-tag list: Spirometry,
   FirstMedication, Medication, SecondMedication, ThirdMedication, Infocard,
   Onboarding; not scheduling-related).

## Writes

- **Monitoring toggle, deactivated then left off.** Blocked from clicking it
  via automation by the Claude Code auto-mode classifier (a live-state
  change); the user clicked it by hand after confirming it was fine. Not
  turned back on at the end of the session — should be revisited if this
  coaching is used for anything monitoring-dependent before then.
- **Accidental rule re-save.** Closing the "Edit rule:" modal for "If still
  in time, send repeated reminder for spirometry measurement" via its
  "Close" button fired a "The rule has been updated." toast, even though no
  field was touched during the session (only opened to read, then closed).
  The user confirmed this is expected UI behaviour (the toast fires on any
  modal close, changed or not) and that a same-value re-save on this
  sandbox coaching is a non-issue — writes here are logged and low-stakes.
  **Do not assume this is true of other coachings.**

## Findings (see README.md and DESIGN.md for the full writeup)

- **No message-priority or tier field exists anywhere in PMCP.** The "Edit
  micro dialog message:" modal has no timing fields at all. The one
  "Low Priority" string a probe dump surfaced was a node's literal Comment
  text (content), not a schema field.
- **Send delay and answer routing live on the *rule* that starts a dialog**,
  not on the message: "Hour to send message (24h hours, 0 = immediately)",
  "Minutes after sending until message is handled as not answered", and
  "Rules if participant DOES / DOES NOT answer" subtrees, all in the "Edit
  rule:" modal.
  **This confirms the correction now recorded in `README.md` and
  `tools/coaching-bundle-export/DESIGN.md`.**
- **Rule execution semantics**, per the Rules tab's own Info panel: rules
  execute top-to-bottom down the tree, a non-matching rule's children are
  skipped, and execution stops entirely once a rule "solves the issue."
  Interruption/pile-up is emergent from this plus per-rule timing — not a
  P0–P3 tier system (which was our own invented abstraction).
- The rule → micro-dialog trigger link (previously "only weakly present" in
  the Report HTML export) is fully visible live on every "Start micro
  dialog" rule leaf — a scraping gap, not a PMCP gap.

## Tooling fixes made as a result

- `probe_node_editor.py`: `close_windows()` only tried a "Cancel" caption;
  fixed to also try "Close" and "Exit" (all three are used by different
  modals). HTML capture limit raised from 20000 to 60000 chars (some modals
  were truncated). Screenshot calls wrapped so a timeout at the 12000px
  probing width doesn't crash the whole run.
- Found and worked around: a modal left open by an earlier crashed run
  silently blocked every subsequent MenuBar click, masquerading as session
  expiry or the width issue. See root README's hurdles section.

## Session hygiene notes for next time

- Session idle timeout is closer to ~10 minutes than the ~1–2h previously
  assumed (per the user). Don't leave long gaps between live-portal actions.
- A plain `page.reload()` drops the Vaadin SPA back to the login screen even
  with a valid cookie — never use it to "reset" a stuck view.

## Follow-up analysis and replanning (same session)

Reviewing the findings above surfaced a replanning worth acting on
immediately, plus some genuine unknowns to flag rather than paper over.

**Replanning:** workstream 2 (pile-up) doesn't need workstream 3 (the Stage-3
export) finished to get a useful first pass — it needs a human or Claude
reading the live Rules tab's order and timeouts for the reminder rules, which
is fully possible today. Split into 2a (manual pass, unblocked, next
concrete step) and 2b (rigorous bulk pass, still needs Stage 3). Written up
in `README.md`'s roadmap and `TASKS.md`.

**Open questions, not yet resolved** (also in `README.md`'s "Open questions
from today's exploration" and `tools/coaching-bundle-export/DESIGN.md`):
- Two independent rule actions exist ("Send message" vs "Start micro
  dialog") — only the micro-dialog path was sampled.
- "Message group to send messages from" field on the rule form, seen
  blank/disabled — possible second dispatch layer, unexplored.
- Only one rule was sampled overall; field-set consistency across
  UNEXPECTED MESSAGE / USER INTENTION rules and decision-point-level answer
  routing (vs. the rule-level DOES/DOES-NOT-answer subtree) is unconfirmed.
- The Rules tab (`.v-tree`) needs its own scraper — it's a different Vaadin
  widget from the Micro Dialogs `.v-menubar`.
- Rule-tree row icons likely encode action type; not yet mapped.

**Left as-is, deliberately:** Monitoring stays deactivated on this sandbox
coaching for now (user's explicit call, 2026-09-09) — do not re-enable
without asking.
