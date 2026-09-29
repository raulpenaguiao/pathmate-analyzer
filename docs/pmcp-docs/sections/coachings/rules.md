# Rules

Source: https://my.pathmate.app/pmcp-documentation/doc-6-0/sections/coachings/rules · fetched 2026-09-29 · near-verbatim extract

"Rule" has three meanings: (1) **global execution rules** that trigger micro dialogues, (2) **dialogue-level rules** (message conditions, decision points), (3) **rule types / operators**.

## 1. Global execution rules (Rules tab)

These start micro dialogues, update variables, react to user actions and schedule time-based interactions. They are reorganisable by drag & drop.

### Execution types

| Type | Behaviour | Use | Avoid |
|---|---|---|---|
| **DAILY BASIS** | Evaluated once a day at 00:00, with variables in their 00:00 state. "Scheduled Micro Dialogues sent later in day." "Day-time changes don't affect already-scheduled actions." Processed top to bottom. | daily fixed-time messages, monthly reminders, daily variable updates (e.g. refreshing `$today`) | triggering on the registration day before 00:00 |
| **PERIODIC BASIS** | Runs "approximately every few seconds". "Resource-intensive; use carefully." | first-day dialogues at a user-defined time, frequently changing conditions, immediate feedback after a measurement | predictable fixed-time events (use DAILY) |
| **UNEXPECTED MESSAGE** | For free text arriving "without an open question" (SMS, WhatsApp): this rule tree is evaluated. | e.g. a help dialogue on "help" | |
| **USER INTENTION** | In-app actions set `$participantIntention` (name) and `$participantIntentionContent`. | e.g. `$participantIntention` = "go" after onboarding → start the START dialogue | |

Dialogues can be triggered by time-, event- or variable-based conditions, or combinations.

**Example: weekday.** `$systemDayInWeek calculated value equals 1` → every Monday. (Note: the variables page lists `$systemDayOfWeek`; this example uses `$systemDayInWeek`. ALEX uses `$systemDayInWeek`.)

**Example: inactivity reminder** (DAILY):
1. `$participantLastLoginDate calculate date difference in days and always true $today` → `$daysSinceLastLogin`;
2. `$daysSinceLastLogin calculated value is bigger or equal than 3`;
3. send at 8 AM.

Plus a decision point at the top of the dialogue: `$participantLastLoginDate calculate date difference in days and true if zero $today` → **stop if TRUE**. This re-checks at send time because the rule was evaluated at 00:00. That pattern (**re-check relevance inside the dialogue at send time**) is the docs' only example of guarding against stale sends.

## 2. Dialogue-level rules

- **Message conditions:** the message is sent only if **ALL** rules are TRUE. Example: `$onboardingCompleted calculated value equals 1`.
- **Decision point rules:** branch to messages, jump to or cascade into other dialogues, create variables. **AND = child rules; OR = rules on the same level.** Processed top to bottom.

## 3. Operators

Only predefined variables can be used; unknown ones are an error.

### Text
- `text value (not) equals`: exact match, **case-insensitive, whitespace trimmed**; works with select-one/many. Select-many is stored as comma-separated positions, e.g. Apple+Banana of 1/2/3 → `1,,3`, so `text value equals 1,,3`.
- `text value (not) matches key`: OR over keys, e.g. `matches key 1,3`.
- `text value (not) matches regular expression`: **anchored**; use `.*x.*` for a substring. E.g. `fr.*`, `.*CH`.
- `text value from select many at position`: picks from a pipe-separated variable by an index variable (e.g. `Breathing Exercise 😮‍💨|Meditation 🧘`).
- `text value from multilingual array at position`: the same, for a multilingual array variable.

### Numeric
- `calculated value (not) equals`, `is bigger (or equal) than`, `is smaller (or equal) than`.
- Math: `+ - * / % ^ ()`, `abs ceil floor round min max sum avg sqrt sin cos tan ln log exp random`, `pi e`.
- Platform functions: `first(…)`, `second(…)`, `third(…)` (1-based position of the largest), `position(k, …)`, `digit(k, n)`, **`inrange(v, min, max)`** → 1/0.
- ⚠️ "Missing or non-numeric variables treated as `0` in calculations." Watch out for float artefacts (`1.6000000000000014`); use `round()`.

### Creating variables (always TRUE; `_ALWAYS_FALSE` variants store without branching)
- `calculate value but result is always true` → store to a variable.
- `create text but result is always true`: concatenation. Modifiers: `{#d}` date dd.mm.yyyy, `{#D}` localised date, `{#t}` hh:mm, `{#T}` localised time, `{%.2f}`.

### Date / time
Times are stored as decimals (hh.mm); display with `{#t}`.
- `date difference value equals N`
- `calculate date difference in days/months/years and true if zero`: months = 30.4375 days (use JavaScript for calendar-exact results).
- `calculate date difference in days/months/years but result is always true`: **left date subtracted from right**.
- `calculate new date by adding x days/months/years`

### Advanced
- `text value from json by json path`: enter the path without the leading `$` (`.data.score`).
- **`extract minutes since last variable update`**: minutes since the variable was last written; `-1` if it doesn't exist or has no timestamp. Useful for recency checks (and for response-latency or expiry logic).
- **JavaScript rule**: multi-step calculations, API calls, calendar-exact dates, sensor data. Results are stored directly as participant variables (there's no store-to field) and the rule is always TRUE. See [javascript-snippet](javascript-snippet.md).

## Not on this page (checked)
"Does not answer" / not-answered follow-up rules, sending-rule timeouts ("minutes after sending until message is handled as unanswered"), the order or priority between competing global rules beyond "top to bottom", what happens when a rule fires while a question is open, and whether a variable set by one rule is visible to later rules in the same PERIODIC pass.
