# Micro Dialogs

Source: https://my.pathmate.app/pmcp-documentation/doc-6-0/sections/coachings/micro-dialogs · page says "Last updated: February 2026" · fetched 2026-09-29 · near-verbatim extract

## 1. Concept

A Micro Dialogue is a self-contained conversational unit made of **messages, decision points and events**. Coachings are composed of many reusable micro dialogues instead of one long conversation.

**Structure ≠ flow.** "Micro Dialogues help organise content for authors and editors. They do **not** define the order in which participants experience the coaching." The flow is controlled by rules, conditions, decision points and events.

## 2. Structuring

- Modular design: each dialogue has a clear purpose, can be understood independently, and can be reused.
- **Parent dialogues / sub-dialogues** exist "only inside the editor" and have "no impact on the coaching flow".
- Split out a dialogue when it has a clear task, could be reused, is likely to change, has more than a few messages, or can be explained independently.
- **Cascading for reuse** (motivation check-ins, reflection, goal reviews, feedback loops): create once, cascade into it from many places.

## 3. Creating and configuring

Micro Dialogues tab → **New Dialog** → name. Dialogue properties:
- **Comment**: internal notes.
- **Identifier (optional)**: a unique id that coaching logic can reference.
- **Variable Prefix (optional)**: restricts variable names generated in this dialogue; used for local variables (see [units](units.md)).
- **Assigned Units (optional)**.

## 4. Organising in the editor

Parent: select the leftmost "." dialogue next to START → New Dialog. Sub-dialogue: select the parent → New Dialog (nesting can go deeper). **Move Dialog Before / After / Into** changes the editor view only, "not … runtime behaviour". Rename. Duplicate (copies all content; rename immediately). **Delete is permanent and cannot be undone.**

## 5. Dialogue content

Elements: **Messages**, **Decision Points**, **Events** (trigger Service Channel News or other system actions).

**Message Configuration Table** columns: Type · Comment · Message Text / Events · Channel · Answer Type · Result Variable · **Randomisation Group** · Command Message · Contains Media Content · Contains Link to Survey · Contains Rules (number of conditions).

### Messages
Can show text, include variable placeholders and media, and expect a response or not. They can be conditional: sent only if all rules are true.

### Decision points
- Control the flow within and between micro dialogues, and create or modify variables.
- Combine rules with AND / OR.
- Show no content themselves.
- "They are processed from top to bottom in the order they appear in the Message Configuration Table."

**Order = execution order.** "The system processes all elements from top to bottom … the visible order in the interface defines the execution order." Rearrange with **Move Up / Move Down**.

**Message rules:** the section "Message will only be sent if the following rules are ALL TRUE:" → **+ New** → pick a variable, condition type and comparison value, plus an optional comment. "Only predefined variables can be used. Unknown variables are rejected by the system."

**Jump within a dialogue:** + New Decision Point → rules → *Jump to dialogue message if TRUE* / *if FALSE*. The dialogue "will immediately continue at the selected target message".

### Flow between micro dialogues

| | Jump (**Jump to other dialogue if TRUE**) | Cascade (**Cascade to other dialogue if TRUE**) |
|---|---|---|
| Effect | "The current dialogue is exited. The coaching continues in the target dialogue. The original dialogue is **not** resumed." | "The system temporarily switches to another Micro Dialogue. After the cascaded dialogue finishes, execution returns to the original dialogue. The coaching continues from the point it left." |
| Use for | switching to a different phase; permanently transferring control | reusable sub-dialogues, assessments, modules |

Note (ours): a jump to another dialogue targets the whole dialogue. No "jump to message X of another dialogue" is described.

**Creating variables in decision points:** compute values, aggregate responses, store derived metrics. Variables must be predefined.

**Best practices:** keep branching readable and commented; avoid deeply nested jumps; cascade reusable logic; mind the top-to-bottom order; test every branch.

## 6. Creating messages

**New Message.** Placeholders: `Your average blood pressure was $bloodPressureAverage mmHg.` Format: **Plain** (no HTML) or **HTML** (formatting and links). A response can be expected: "the coaching can wait until the participant replies", the reply can be stored in a variable, and it can influence later logic.

## 7. Answer types

Select options map to codes, and the code is stored. Open input stores the full text.

| Answer type | Behaviour / options |
|---|---|
| Select One | a row of buttons; `button` text + `value` |
| Select Many | `min`/`max`; prefix `! ` = exclusive option (e.g. "! None of the above"), and the `!` is stripped from the label |
| Free Text | placeholder; `textBefore`/`textAfter` via the `_` separator; `ai-free-text` for AI messages |
| Free Text Multiline | `multiline: true` |
| Free Numbers | `onlyNumbers: true`, `min`, `max`, `_` separator |
| Date / Time / Date and Time | `mode: "date"`/`"time"`/`"datetime"`; `placeholder`, `min`, `max` |
| Likert | `label` + `value`, with an explicit confirmation |
| Likert Silent | submits immediately on tap |
| Likert Slider | a horizontal slider with confirmation |
| Image / Audio / Video | upload; an optional `variable`; position via `$systemLinkedMediaObject` (default: end of the bubble) |

Examples, **one option per line**:
```
First answer option:1
Second answer option:2
! Fourth answer option:4        (select many, exclusive)
Name: _                         (free text)
_ EUR                           (free numbers)
Select date\nmin:03.03.2018\nmax:04.04.2018
Select time\nmin:10\nmax:23.5   (times are decimal hours)
very bored:0 … very excited:5   (likert)
```
Custom answer types can be defined by the coaching creator.

Note (ours): the docs only show **literal** min/max values for time pickers. ALEX uses variables there (e.g. `max:$userSetBedtime`), a live precedent the docs don't cover.

## 8. Structural message patterns

- **Randomized messages:** one message from a group is shown. They "must share the same group identifier" and "must appear sequentially". Used for A/B tests, variation and less predictability.
- **Looped messages:** a fixed sequence across executions. They share an identifier and **must "not start with the letter 'r'"** (so identifiers starting with `r` mean randomised; that's why ALEX's groups are `r_…`).
- Don't mix the two patterns unintentionally.

## 9. Media

Images PNG/JPG; audio AA/M4A; video MP4 (H.264, AAC). Media appears after the text by default; the position can be set via `$systemLinkedMediaObject`.

## Not on this page (checked)
Deactivate/recall of open questions, the "clears the current dialog cascade" setting, per-message timeouts / "minutes after sending until message is handled as unanswered", blocking vs time-out configuration, what happens when another dialogue starts while a question is open. See [../../README.md](../../README.md#not-documented-anywhere).
