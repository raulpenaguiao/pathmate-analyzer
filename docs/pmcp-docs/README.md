# PMCP v6.0 docs: knowledge base

A local, searchable extract of the official PathMate Coaching Platform docs,
https://my.pathmate.app/pmcp-documentation/doc-6-0, **fetched 2026-09-29** by Mason for Raul, and shared with every agent.

**How to use it**
- Grep here first, then **cite the live URL** (each file starts with it). Per RULES.md, a PMCP behaviour claim needs a docs page or a live precedent.
- The files are **extracts made via WebFetch**: near-verbatim for the key pages (flow, micro dialogs, rules, variables, units), condensed for the rest. Text in "quotes" is verbatim as fetched. Before quoting to someone outside the team, re-check the live page.
- **"Note (ours)"** marks our commentary: relevance to ALEX, gaps, discrepancies. Everything else is what the docs say.
- Refresh it when PathMate updates the docs. Two pages show "Last updated": micro dialogs and units (Feb 2026), MCP (June 2026).

## Index

| File | Docs pages | Why you'd open it |
|---|---|---|
| [best-practices/defining-the-conversational-coaching-flow.md](best-practices/defining-the-conversational-coaching-flow.md) | Defining the Conversational Coaching Flow | **Interruptions, blocking vs time-out questions, priority hierarchy, reactivate vs delete.** The only page on pile-up |
| [best-practices/timing-messages.md](best-practices/timing-messages.md) | Timing Messages | fixed / user-defined / smart / event timing; "message interference" |
| [best-practices/designing-a-coaching-intervention.md](best-practices/designing-a-coaching-intervention.md) | Designing a Coaching Intervention | sample week, master plan, the "lazy user" scenario |
| [best-practices/designing-dialogues.md](best-practices/designing-dialogues.md) | Coaching Dialogues | message length, at most 3 messages before a response, max 10 min |
| [best-practices/user-response-options-and-analytics.md](best-practices/user-response-options-and-analytics.md) | User Response Options, Analytics | answer-option design; the analytics list |
| [best-practices/other-best-practices.md](best-practices/other-best-practices.md) | Best Practices index, Objectives & KPIs, User Onboarding, Start Here | |
| [sections/coachings/micro-dialogs.md](sections/coachings/micro-dialogs.md) | Micro Dialogs | **jump vs cascade**, decision points, top-to-bottom order, answer-type syntax, randomised (`r…`) vs looped groups |
| [sections/coachings/rules.md](sections/coachings/rules.md) | Rules | **DAILY / PERIODIC / UNEXPECTED / INTENTION**, AND/OR, all operators, `inrange`, `extract minutes since last variable update`, "missing vars = 0" |
| [sections/coachings/variables.md](sections/coachings/variables.md) | Variables | system and participant variables, incl. `$participantOpenQuestions`, `$participantOpenDialogCascades`, `…InfiniteBlockingMessages…` |
| [sections/coachings/units.md](sections/coachings/units.md) | Units | variable prefixes; **"Assigned units to reset if TRUE"** resets a topic's locals and keeps the history |
| [sections/coachings/javascript-snippet.md](sections/coachings/javascript-snippet.md) | JavaScript Snippet, MCP Client Integration | the JS rule contract, 60 s timeout, sensor queries, `mcp()`, `llm()` |
| [sections/coachings/basic-settings.md](sections/coachings/basic-settings.md) | Basic Settings and Modules | deactivate before editing; auto-deactivation after 186 days; LLM meta |
| [sections/coachings/participants-results-access.md](sections/coachings/participants-results-access.md) | Participants, Results, Access | monitoring status; Results message statuses; the manual "handled as unanswered" time frame |
| [sections/editor-admin.md](sections/editor-admin.md) | Editor overview, Coachings list, Access Control, Account, Translations | Report/Validate/Duplicate; **1 admin per coaching**; Reset All Locks; CSV translation round-trip |
| [sections/llm-and-events.md](sections/llm-and-events.md) | LLM Integration, Events & Actions | LLM sessions/OneShots/slots; service channel news |
| [communication-channel.md](communication-channel.md) | Channels & Media, plus all 11 subpages | push rules (**smart push: none within 6 h of another**), questionnaires (`validDays`, bindings), **commands**, media library, health data |
| [coach-management-system.md](coach-management-system.md) | Coach Management System, App Screens, Adherence Cockpit | PCMS tabs, screens, daily plan, the **built-in adherence model** |
| [testing-and-data-export.md](testing-and-data-export.md) | Testing, Trouble Shooting, Data Export | `$debug`, debug jump, validation report; **the 7 export CSVs**, incl. `dialog-messages-list.csv` and `variables-history-list.csv` |

## Interruptions and pile-up

**What the docs do say** (all on [the coaching-flow page](best-practices/defining-the-conversational-coaching-flow.md) unless noted):
1. Decide four things per dialogue: blocking or time-out? Interruptible? By whom? Resume or terminate afterwards?
2. **Blocking questions** (the default) "stay active until the user responds". **Time-out questions** "disappear if not answered within that time", for exceptional cases only.
3. When a dialogue is due while a question is open, either it **interrupts** ("The open question is deactivated") or it **queues**.
4. **Hierarchy principle:** "A higher-priority dialogue cannot be interrupted by a lower-priority dialogue, but the reverse is allowed." Also decide the equal-priority case. This is a design principle; **there is no priority setting**.
5. **After an interruption:** Option 1 "(typically used)" reactivates the question with a transition phrase ("Let's get back to our earlier discussion..."). Caution: "requires more sophisticated dialogue state management and careful planning to avoid overwhelming the user with too many interruptions". Option 2 deletes it, "only … where unanswered questions lose relevance".
6. **Jump vs cascade** ([micro-dialogs](sections/coachings/micro-dialogs.md)): a jump never resumes the original; a cascade returns to it.
7. **Related handles:** `$participantOpenQuestions`, `$participantOpenDialogCascades`, `$participantInfiniteBlockingMessages{Count,Identifiers,WaitingMinutesMax,WaitingMinutesMin}` ([variables](sections/coachings/variables.md)), names only. The only stale-send guard shown is re-checking at the top of the dialogue with a "stop if TRUE" decision point ([rules](sections/coachings/rules.md), inactivity example). **Unit resets** ([units](sections/coachings/units.md)) wipe a topic's local variables.
8. "Message interference" is named as a risk of user-defined timing ([timing-messages](best-practices/timing-messages.md)), with no mechanism given.

### Not documented anywhere
Checked across all 49 pages on 2026-09-29:
- the message settings **"Deactivates and remembers all former open questions"** and **"Recalls former deactivated questions from last deactivation"** (used throughout ALEX v01), including what "from last deactivation" means when deactivations nest;
- **`$participantDeactivatedOpenQuestions`** (gates v01's transition line): not listed, no semantics, and it's unclear whether it is per participant or per dialogue;
- the **"clears the current dialog cascade"** message setting;
- the per-message **"minutes after sending until message is handled as unanswered"** timeout for coaching messages, and what happens when it passes (the Results page mentions a time frame only for manual messages);
- **"does not answer" rules** on sending rules;
- any **expiry of deactivated questions** across days;
- behaviour when a global rule fires **while a question is open**;
- whether variables set by one rule are **visible to later rules in the same PERIODIC pass**;
- what an **"infinite blocking message"** is.

Anything the pile-up design depends on from this list must be tested live (see `docs/pileup/rollout.md` step 0) or asked of PathMate.

## Discrepancies spotted
- The weekday variable: the variables page lists `$systemDayOfWeek`, but the rules example (and ALEX) use `$systemDayInWeek`.
- Debug: the docs use `$debug`; ALEX uses `$debugMode`.
- ALEX uses `$timeDecimal` and variable bounds in time pickers (`max:$userSetBedtime`); neither appears in the docs.
