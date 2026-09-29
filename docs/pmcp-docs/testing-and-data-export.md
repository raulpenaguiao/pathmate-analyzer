# Testing · Trouble Shooting · Data Export

Fetched 2026-09-29 · condensed extracts

## Testing
https://my.pathmate.app/pmcp-documentation/doc-6-0/testing

- Install the Mobile Coach app, open the coaching in the CMS and scan the **development QR code**.
- **Debug mode:** the `$debug` variable (1 = testing, 0 = real), set in the Variables tab. Conditional test messages only show when `$debug = 1`.
- **Debug jump:** "jump to a specific dialogue for testing purposes without passing through previous dialogues".
- Restart testing via the debug panel → reset.
- Not on the page: time simulation or offset (`$systemTimeOffsetInMinutes` exists on the variables page), test-participant management, how to test interruptions.

Note (ours): ALEX uses `$debugMode` (e.g. on a transition line), not `$debug`.

## Trouble Shooting
https://my.pathmate.app/pmcp-documentation/doc-6-0/testing/trouble-shooting

- **Validation Report:** an "automated check to identify inconsistencies, formatting errors, and potential issues within the coaching's dialogue content".
- **Results for troubleshooting:** check that variables were logged with the expected values, participants enrolled correctly, messages or rules triggered, and system messages, commands and intentions were sent.
- Nothing on interruptions, repeating transition lines or reappearing questions.

## Data Export
https://my.pathmate.app/pmcp-documentation/doc-6-0/data-export

Coaching → Edit → Results → **Export All Data** gives a zip of 7 CSVs:

| File | Content |
|---|---|
| `basic-participation-table.csv` | 34 participant-level fields (logins, language, organisation, unread counts…) |
| `dialog-messages-list.csv` | **35 fields per coaching message: content, answer type, delivery status, timestamps, cascade identifiers** |
| `dashboard-messages-list.csv` | dashboard channel messages |
| `json-objects-table.csv` | JSON questionnaires |
| `json-sensor-data-list.csv` | sensor data |
| `variables-history-list.csv` | **every variable's historical values with timestamps** |
| `variables-table.csv` | current variables with timestamps |

Timestamps are **unix seconds**.

**Relevance (ours):** `dialog-messages-list.csv` (delivery status + timestamps per message) might already record sent-vs-answered, i.e. ignored prompts and latency. That's open question 1 in `docs/participant_data_collection.md`, and worth checking against a real export before adding counters. The 35 column names are not listed in the docs.
