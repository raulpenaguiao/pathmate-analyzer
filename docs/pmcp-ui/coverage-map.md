# Export coverage map

**Owner:** Mirror. This is a living document: update it whenever an export,
a screenshot, a live look or a PathMate answer changes a row.
**Last checked:** 2026-10-01, against
`data/exports/coaching_alex-v01-zum-ausprobieren-2_20261001-134557.json`
(alex-live).

The map has one row per option in the PMCP editor, grouped by object.

| Column | Values |
|---|---|
| **In .json** | **yes** · **partial** (some of it, or read indirectly) · **no** |
| **Sim needs** | **now** (EngineV1 already depends on it or gets it wrong) · **soon** (needed for the pile-up design or ALEX v02) · **later** · **no** (no effect on what the patient sees or which variables change) |
| **Meaning** | **doc** (PMCP 6.0 docs, extracted in `docs/pmcp-docs/`) · **live** (seen in the editor or in exported data) · **inferred** · **unknown** |

Only the **.json export** counts here: that's our exporter reading the editor
tables. The **.html export** (the Report from PMCP's Export button) is only
an input to it.

**The split of authority with Mason's editor documentation:** what a
setting *means* (Confirmed / Inferred / Unknown) is settled in
[PMCP editor: what every setting does](https://claude.ai/code/artifact/27405faa-5de0-4e32-a865-c5de349ef0cb).
This map settles whether a setting is *exported* and whether the *engine
uses it*. Mason copies those two columns into his doc. Where the Meaning
column here and his doc differ, his doc wins; tell Mirror so this map can
be fixed. For example, ALEX has **21 custom answer types**, which aren't
covered in §3 yet.

Sources:
- Raul's notes and screenshots: `docs/pmcp-ui/raul-2026-10-01/`
- Mason's live look on 1 Oct:
  [The rule editor's greyed-out options](https://claude.ai/code/artifact/35542fec-3001-4795-b570-df78f9405bd6)
- `docs/pmcp-docs/`

## Summary

- **The export spec for Warden:** 14 rows, in section 6.
- **The open meanings for Mason and PathMate:** 13 rows, in section 7.
- **The engine's current assumptions:** section 8.
- **Questions to ask about each dialog:** section 9.

Two results that come from the export itself, not from the editor:

- **The answer tabs and the not-answered time are really used only with
  "Send message".** On alex-live, the only "Send message" rule is `r-071`,
  the spirometry reminder, which is switched off and sends from message
  group "Test". It's the only rule with a non-default not-answered time
  (19 min) and with filled DOES and DOES NOT answer rules. Of the 36 "Start
  micro dialog" rules:
  - 28 have `notAnsweredTimeout` disabled;
  - 8 have it enabled but left at the 240-min default: r-097, r-110,
    r-123, r-143, r-144, r-145 (debug, sensor and settings-change rules)
    and r-147, r-155 (USER INTENTION).

  So the editor's enabled state doesn't follow the action box alone. It
  partly supports Mason's reading 1, that the tabs work together with a
  message group, but doesn't prove it.
- **Time answers are stored as decimal hours.** The docs say so in their
  input-format example: "Select time … min:10 max:23.5 (times are decimal
  hours)" (`micro-dialogs.md` §7). The engine already stores time answers
  this way (`dbfc05d`), so that assumption is now confirmed by the docs.

## 1. Rules (Rules tab, "Edit rule")

| Option | In .json | Sim needs | Meaning | Open question |
|---|---|---|---|---|
| Execution type: DAILY BASIS | yes (`section`) | now | doc: runs at 00:00, and later sends wait for their hour | — |
| Execution type: PERIODIC BASIS | yes | now | doc: runs "approximately every few seconds" | the order of rules within one pass (same-pass visibility is pile-up test A2, now an engine switch) |
| Execution type: USER INTENTION | yes (2 rules) | later | doc: in-app actions set `$participantIntention` | the engine never runs this tree; it needs a "user action" input |
| Execution type: UNEXPECTED MESSAGE | **no** (not among the export's sections) | later | doc: free text arriving with no open question | Does ALEX have none, or does the exporter miss the section? |
| Rule tree: nesting, order and depth | yes (`ruleTree`, `depth`, `parentUid`) | now | doc: a child rule ANDs with its parent, and siblings are separate (OR) | — |
| Condition (x, operator, y) | yes (`expr`, structured) | now | doc: operators are in `rules.md` §3 | JS-snippet rules can't be evaluated |
| Pure condition (no action box ticked) | yes (`kind: condition`) | now | live | — |
| Action: send message (message group) | yes (`primaryAction`, `messageGroup`) | soon | unknown: no doc on message groups | What a message group is. The **engine doesn't model message groups on the bundle path**: it only logs "sends a message". |
| Action: start micro dialog | yes (`microDialogToStart`, `microDialogPath`) | now | live | What happens to an open question from another dialog (PathMate Q4). The engine suppresses and retries, an assumption. |
| Action: mark case solved + stop the run | yes (`actionBoxes`, `primaryAction`) | soon | unknown | Does it stop the rest of a periodic pass? The engine doesn't model it. |
| Action: stop the run + finish the coaching | yes | later | inferred: it ends the coaching | The engine only logs it. ALEX must never use it. |
| Hour to send message | yes (`sendHourVariable` / `sendHourClock`) | now | doc + live: a decimal hour, 0 = immediately | What happens if the hour has already passed, or two dialogs are due at once (PathMate Q7). The engine fires late the same day. |
| Not-answered time (minutes) | yes (`notAnsweredTimeoutMinutes`) | now | live: disabled on 28 of 36 "Start micro dialog" rules; the only non-default value is on the one "Send message" rule | It covers which messages? (Q8). **The engine applies it to every sender's questions, including rules where the editor disables it.** |
| Store result variable | partial: it reads "Test (expects NO answer)", the message-group text | soon | unknown | Is it a scraper bug (it duplicates `messageGroup`)? |
| Rules if participant DOES answer | partial: captions only (`doesAnswerRules`, 1 rule) | soon | unknown | When do they run (Q8)? A caption is not an evaluable expression. |
| Rules if participant DOES NOT answer | partial: captions only (1 rule) | soon | unknown | Do they run once, after the not-answered time (Q8)? This is pile-up test A3. |
| Field enabled / disabled state | yes (`disabledFields`, `answerTabs[].disabled`) | no | live | `answerTabs.disabled` is False on all 37 rules, yet Mason saw them greyed out. Does the scraper read the wrong attribute? |
| Comment | no (empty on 37 of 37 sending rules) | no | — | — |

## 2. Micro dialogs (properties)

| Option | In .json | Sim needs | Meaning | Open question |
|---|---|---|---|---|
| Name, folder path, nesting | yes | now | doc | — |
| Comment | no | no | doc | — |
| Identifier (optional) | **no** | soon | doc: "a unique id that coaching logic can reference" | A stable id across exports would fix "uids are positional". What does `$participantNextMicroDialogIdentifier` refer to? |
| Variable prefix | no | later | doc: local variables (`units.md`) | — |
| Assigned units | no | later | doc: `units.md` | — |
| Order of elements | yes (node order) | now | doc: top to bottom | — |

## 3. Messages ("Create micro dialog message")

| Option | In .json | Sim needs | Meaning | Open question |
|---|---|---|---|---|
| Comment | yes | no | — | — |
| Text format (plain / HTML / …) | partial (`textHtmlByLang` on 10 messages) | later | live | — |
| Text, per language | yes (`textByLang`) | now | doc | — |
| Integrated media / media title | partial (`mediaFile` only) | no | doc | — |
| Linked intermediate survey | partial (`flags.containsSurvey`) | later | unknown | Which survey, and does it block like a questionnaire button? |
| Message key | **no** | soon | unknown (label: "must not be unique") | Is this the looped-message identifier (`micro-dialogs.md` §8)? |
| Randomisation group | yes (`randomisationGroup`) | now | doc: groups starting with `r` are randomised, others are looped | **Looped (non-`r`) groups aren't modelled.** The engine treats every group as random. |
| Command (invisible) | yes (`commandByLang`, `flags.commandMessage`) | now | live | Which commands change state (e.g. `set-achievement`)? |
| Expects an answer | partial: read from `answerType` | now | live | — |
| Answer type (25 types) | yes | now | doc for 12 of them; the editor lists 25 (screenshot shows 1–10) | The other 13 types are unseen. The engine treats every free text / free numbers / date / time variant, "raw" included, as a typed input. |
| Answer options | yes (`answerOptionsByLang`) | now | doc: `label:value`, `_`, min/max | — |
| Store reply to variable | yes (`resultVariable`) | now | doc | — |
| **Value stored on no reply** | **no** | **now** | inferred from the label | An ignored question should write this value. The engine writes nothing. |
| Channel | yes | no | doc | — |
| Answer can be cancelled (no value set) | no | later | label only | — |
| **Blocks the micro dialog until answered/unanswered** | **no** | **now** | label only | The engine treats every question as blocking. Non-blocking questions would let the dialog continue. |
| Sticky in the client | no | no | unknown | — |
| Only a push notification / always pushed | no | later | doc (push pages) | — |
| **Deactivates and remembers former open questions** | **no** | **soon** | unknown | Used by v01 to park interrupted questions (PathMate Q15) |
| **Recalls deactivated questions (last / most recent still filled)** | **no** | **soon** | unknown | Q15 |
| **Clears the current / all dialog cascades** | **no** | **soon** | unknown | Pile-up test A1, Q16 |
| Not cleared on "clear all" | no | soon | unknown | Q16 |
| **Minutes until handled as unanswered (per message)** | **no** | **now** | label only | A per-message timeout, separate from the rule's. Which one wins? "infinite" may be what `$participantInfiniteBlockingMessages*` counts (Q17). |
| Message rules (all must be TRUE) | yes (`triggerExprs`) | now | doc: AND, no nesting | — |

## 4. Decision points ("Create rule" inside a decision point)

| Option | In .json | Sim needs | Meaning | Open question |
|---|---|---|---|---|
| Decision point comment | yes | no | — | — |
| "Update transition point" | **no** | unknown | unknown | What it is (Raul's notes) |
| Rule tree (AND = child, OR = sibling) | yes (`branches`, `depth`, `parentIndex`) | now | doc | — |
| Rule comment | yes | no | — | — |
| Condition, operator, comparison | yes (`condition`) | now | doc | — |
| Store result to variable | yes (`writesVar`) | now | doc | — |
| Leave this decision point if TRUE (jumps still run) | partial: the field exists but is empty on all 875 branches | now | label | Is it never used, or never scraped? Check one live example. |
| Stop this micro dialog if TRUE | yes (`stopMicroDialog`) | now | label + live | — |
| Update participant to a newer coaching if TRUE | **no** | no | label | Never used in ALEX? |
| Assigned units to reset if TRUE | **no** | later | doc: `units.md` | — |
| Cascade to another dialog if TRUE | yes (`cascadeDialog`) | now | doc: returns to the caller | — |
| Jump to another dialog if TRUE | yes (`jumpDialog`) | now | doc: doesn't return | — |
| Jump to a dialog message if TRUE / FALSE | yes (`jumpMessageIfTrue/False`): 24 resolved live, some still ambiguous | now | doc | Warden's `--resolve-jumps` still isn't stable on long dialogs |

## 5. Events and variables

| Option | In .json | Sim needs | Meaning | Open question |
|---|---|---|---|---|
| Event element in a dialog | **no** (the exporter emits only message/decision nodes) | later | doc: "trigger Service Channel News or other system actions" | ALEX has none, but would the exporter even see one? |
| Event comment / identifiers / rules | no | later | unknown: an identifier "starts with a dot"? (Raul) | What are the identifiers? |
| Variable name and start value | yes | now | doc | — |
| Privacy / access / auto sync / sensitive | yes | no | doc: `variables.md` | "Manageable by service" variables may be set from outside the chat. Should the simulator offer them as settings? |
| Multilingual array variable | yes | now | doc (flag); the value format is an assumption (`dbfc05d`) | — |
| Questionnaire → variable bindings (PMCMS) | **no** | now | doc: the questionnaire button blocks the chat | Where the bindings live, and whether we can read them |

## 6. Export spec: needed but missing (for Warden)

These are ranked by what the simulator needs first. Warden does **one
batched live pass**, sandbox first. Most message settings aren't in the
Report, so they need a read of each message's editor.

1. **Messages: "Store the following value in case of no reply".**
2. **Messages: "Minutes after sending until message is handled as
   unanswered"** (per message, including "infinite").
3. **Messages: "blocks the micro dialog until answered/unanswered".**
4. **Messages: the memory settings** (deactivates/remembers, recalls from
   last, recalls from most recent still filled). Export as one enum field.
5. **Messages: the cascade settings** (clears current, clears all, not
   cleared on clear all). Export as an enum field plus a boolean. This
   covers pile-up test A1.
6. **Rules: DOES / DOES NOT answer as evaluable expressions**, not just
   captions. Export them with the same structured `expr` the rule tree uses.
7. **Rules: the UNEXPECTED MESSAGE section**, if it exists (check whether
   it's missing or empty).
8. **Micro dialogs: Identifier, variable prefix, assigned units.** The
   identifier also gives stable ids across exports.
9. **Messages: Message key**, the looped-message identifier.
10. **Messages: "answer can be cancelled", "sticky", push-only / always
    pushed, linked survey name.**
11. **Decision rules: "Update participant to newer coaching", "Assigned
    units to reset", and a check on "Leave decision point"** (0 of 875
    filled).
12. **Decision points: "Update transition point".**
13. **Events: comment, identifiers, rules.** Make sure the exporter emits
    event nodes at all.
14. **Fixes to check:**
    - `storeResultVariable` shows the message-group text;
    - `answerTabs[].disabled` is False on all 37 rules, but Mason saw the
      tabs greyed out.

## 7. Open meanings (for Mason and PathMate)

Numbers refer to Herald's PathMate email, v8 (22 questions):
`agents/herald/context/drafts/pathmate-email/draft.md`.

| # | Option | Question | Email |
|---|---|---|---|
| 1 | Message group | What it is, and when to use it instead of starting a dialog | Q3 |
| 2 | Mark case solved | Does it also stop a periodic pass? | Q5 |
| 3 | Hour to send | The hour has already passed, or two dialogs are due at once | Q7 |
| 4 | Rule not-answered time | Is it really only for "Send message"? Does it cover the first message or every question? | Q8 |
| 5 | DOES / DOES NOT answer | When they run | Q8 |
| 6 | Starting a dialog while a question is open | Is the open question deactivated, queued or removed? | Q4 |
| 7 | Same-pass visibility | Do later rules in a pass see earlier writes? | Q2 |
| 8 | Memory settings | Parking and recall, last vs most recent still filled | Q15 |
| 9 | Cascade settings | Clear current / clear all / exempt | Q16 |
| 10 | Per-message "minutes until unanswered" vs the rule's | Which one applies; what "infinite" means | Q17 |
| 11 | Value stored on no reply | Is it written when the timeout passes? | Q17 |
| 12 | Message key | Is it the looped-message identifier? | Q9 |
| 13 | Update transition point; update participant to newer coaching | What they do | Q18, Q19 |

## 8. What the chat engine assumes today

This is where EngineV1 (`app/coaching_sim.py`) settles the open meanings
above. Each item is an assumption until a doc, a live test or PathMate
confirms it.

| Behaviour | Engine today | Basis |
|---|---|---|
| Jump vs cascade to another dialog | Jump exits for good. Cascade returns to the calling dialog, at the next element. | doc (`micro-dialogs.md` §5) |
| Decision point | Runs every rule top to bottom; assignments always apply. The first TRUE rule with a jump, cascade or stop acts on it. | doc (top to bottom) + inferred (first acting rule wins) |
| Blocks / sticky / cancellable | **Every question blocks** its dialog until it's answered or times out. Sticky and cancel aren't modelled. | assumption: the setting isn't exported |
| Per-message "minutes until unanswered" | **Not modelled.** It isn't exported, so it behaves like "infinite". | assumption |
| Rule-level not-answered time | Applies only to questions in a dialog a sender started. On timeout, the whole dialog and its cascade callers are abandoned, and **nothing is written** (no "value on no reply"). DOES NOT answer rules are logged, not run. | assumption |
| Dialog starts while a question is open | The sender is **suppressed** and retries on later ticks. | assumption (Phase D); PathMate Q4 |
| Same-pass visibility | Visible at once. It's a switch: `settings.same_pass_visibility`. | assumption (A2) |
| Memory and cascade message settings | Not modelled | not exported |
| Randomisation groups | Every group is random; one seeded pick per run | doc for `r_` groups; looped groups aren't modelled |
| Time / date answers | Time is a decimal hour; dates are dd.mm.yyyy as typed | doc (time); assumption (date) |
| Multilingual variables | The sim language's part of `en-GB: … / ro-RO: …` | assumption |
| Send hour already passed | Fires on the next tick the same day, once per day | assumption; PathMate Q7 |

## 9. Questions to ask about each dialog

Raul asked for these. For every micro dialog, the simulator, and anyone
reviewing it, should be able to answer the questions below. Most come
straight from the export. The ones marked * need fields from section 6.

1. **What starts it?** A rule (which type, which hour, which gate), a jump
   or cascade from another dialog, a user intention, or nothing (an
   orphan).
2. **What can stop it before it starts?** Re-check gates at the top of the
   dialog, as in the docs' inactivity example.
3. **What does it ask?** Each question's answer type, options, and the
   variable it writes.
4. **What happens if the patient ignores it?** The not-answered time, the
   value stored on no reply*, whether it blocks*, and any DOES NOT answer
   rules.
5. **What happens if another dialog interrupts it?** Its memory and cascade
   settings*, and whether it comes back from the start (pile-up design).
6. **Where can it go?** Jumps (it doesn't return) and cascades (it
   returns), with the condition for each.
7. **What does it change?** Every variable it writes, in decision points
   and in answers.
8. **Which variants can the patient see?** Its randomisation and looped
   groups.
9. **Can it repeat?** Same-day re-launch, daily senders, and the
   once-a-day key.
10. **What isn't modelled?** JS rules, commands with side effects, events,
    and questionnaire bindings. These are the places where the simulator
    could be wrong for this dialog.

Next step (Mirror): generate these answers for every dialog from the
export, as a per-dialog sheet, so each dialog's gaps are visible
one by one.
