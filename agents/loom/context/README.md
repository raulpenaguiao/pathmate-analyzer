# Loom's private context

Free-form notes only Loom needs: future tasks, quirks/skills learned
on the job, anything not meant for anyone else. Not a mailbox - nobody
else is expected to read this folder, and this agent shouldn't expect
anyone to.

## Wake-up sequence (Raul, 2026-09-29)

1. Read RULES.md, every AGENT.md, my STATUS.md and this folder.
2. `agents/checkmail.sh loom` and process everything.
3. **Start the mailbox listener** (RULES.md rule 5). Use the `Monitor` tool
   (allow-listed, no prompt; NOT a Bash background loop) with
   `timeout_ms: 1800000`, description "new mail in Loom's inbox":
   ```
   d=/home/raul/projects/pathmate-analyzer/agents/loom/mailbox/inbox
   prev=$(find "$d" -maxdepth 1 -name '*.md' 2>/dev/null | wc -l)
   while true; do
     n=$(find "$d" -maxdepth 1 -name '*.md' 2>/dev/null | wc -l)
     [ "$n" -gt "$prev" ] && echo "new mail: $n unread (was $prev)"
     prev=$n
     sleep 60
   done
   ```
   Monitor expires after 30 min at most: **re-arm it on every expiry notice.**
   On a "new mail" event, read it with plain `checkmail.sh` calls.
4. Check mail by hand right before any live browser run and after each step.
5. State codename and role, then resume the next step from STATUS.md.
