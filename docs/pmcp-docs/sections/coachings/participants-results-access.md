# Participants · Results · Access

Fetched 2026-09-29 · condensed extracts

## Participants
https://my.pathmate.app/pmcp-documentation/doc-6-0/sections/coachings/participants

For managing individuals, mostly in the live phase.
- **Columns:** Participant ID, Name (a nickname), Language, Group, Organisation, Organisation Unit, Created, Assigned Survey / Survey Status (legacy), Data for Monitoring Available ("whether all necessary data for initiating the coaching process with a participant is present"), Coaching Status (finished / not finished), **Monitoring Status** (when inactive, "no rules or messages will be processed"), Deactivation Status.
- **Functions:** Import/Export (CSV), Assign Group/Organisation/Unit, Delete, Refresh, **Switch Monitoring**, Send Message.

## Results
https://my.pathmate.app/pmcp-documentation/doc-6-0/sections/coachings/results

- **Participant details**, **Message Dialogs** ("Lists all messages sent to participants, including their status (e.g. 'sent but not waiting' indicates that a message has been sent and no reply is awaited)"), and **Variables with Values**.
- **Export All Data:** select participants → Export All Data → CSV with details, responses, system variables and collected data.
- **Edit** a participant's variable value directly.
- **Send Message** manually: pick a channel (app/partner, SMS, email), compose it, optionally add variables, and "Define the time frame for handling the message as unanswered, which is crucial for follow-up processes".

Note (ours): this is the only place the docs mention the "handled as unanswered" time frame, and only for manual messages. The coaching-message version ("minutes after sending until message is handled as unanswered") isn't documented, and neither is what happens once it has passed. The message statuses beyond "sent but not waiting" aren't listed.

## Access
https://my.pathmate.app/pmcp-documentation/doc-6-0/sections/coachings/access

Per-coaching Access tab: pick a user → **Add**; select → **Remove**. See [access-control](../editor-admin.md#access-control).
