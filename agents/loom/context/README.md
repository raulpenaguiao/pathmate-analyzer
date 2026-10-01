# Loom's private context

Free-form notes only Loom needs: future tasks, quirks/skills learned
on the job, anything not meant for anyone else. Not a mailbox - nobody
else is expected to read this folder, and this agent shouldn't expect
anyone to.

## Wake-up sequence (Raul, 2026-09-29)

1. Read RULES.md, every AGENT.md, my STATUS.md and this folder.
2. `agents/checkmail.sh loom` and process everything.
3. **Start the mailbox listener** (RULES.md rule 5, Raul 10-01): run
   `agents/waitmail.sh loom` as a background Bash command
   (run_in_background: true). It's allow-listed with no time limit, and exits
   only when unread mail is waiting. Then read with plain `checkmail.sh` and
   start it again. NO Monitor loops: the 30-min restarts flooded Raul's
   terminal.
4. Check mail by hand right before any live browser run and after each step.
5. State codename and role, then resume the next step from STATUS.md.

## NO API calls from Loom (Raul 09-30, RULES.md)
Never run rgroup_expand.py (or anything calling the Anthropic API), not even a
one-call probe. Stop after prepare, then hand the run to the MANAGER session
with the requests file + call/variant counts. --resume runs are the
manager's too.

## PMCP docs knowledge base (Mason, 09-29): docs/pmcp-docs/README.md
- micro-dialogs.md §8: a randomised group shares one identifier, and its rows
  must be sequential (= apply's Move Up adjacency). Looped groups must NOT
  start with 'r'.
- sections/editor-admin.md 'Translations': documented CSV export/import of
  all message text (needs the coaching deactivated). It could bulk-EDIT
  existing text (e.g. the ro-RO repeats, the typo), but it can't ADD rows
  (docs: "don't change the row or column structure", translations page),
  so apply's row-by-row duplicate is still needed for new variants. Worth
  checking if a text-only fix pass is ever needed.

## Future: r_ apply on the workbench coaching (Mason, 09-29)

apply duplicates an existing row of the group, so copies inherit its
options. Before applying to the workbench spirometry dialog, check that
the source row's options are correct (Yes:1 / No:0 on TWO lines). The
sandbox's Stage3 rows have them on one line (the bug); don't carry that over.
