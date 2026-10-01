# Smith's private context

Free-form notes only Smith needs: future tasks, quirks/skills learned
on the job, anything not meant for anyone else. Not a mailbox - nobody
else is expected to read this folder, and this agent shouldn't expect
anyone to.

## Wake-up sequence (Raul, 2026-09-29)

After the startup reads (RULES.md, every AGENT.md, own STATUS + context):

1. `agents/checkmail.sh smith`, then read and act on each message.
2. **Start the mailbox listener (Raul, 10-01):** `agents/waitmail.sh smith`
   as a **background Bash command** (run_in_background). It's allow-listed, has
   no time limit, and exits only when unread mail is waiting. **No Monitor
   loops** (their 30-min restarts flooded Raul's terminal).
3. When it exits: read with the plain `checkmail.sh` forms, then start it again.
4. Then state codename + role and resume STATUS's next step.

## PMCP docs: local KB first
`docs/pmcp-docs/` (Mason, a2cb347): all 49 v6.0 pages, one file per area,
with source URLs. Start at its README and grep before WebFetch. Portal-relevant:
`testing-and-data-export.md` (7 'Export All Data' CSVs, e.g.
dialog-messages-list.csv with delivery status) and `sections/coachings/rules.md`
(full operator reference).
