# Agent rules

This repo is worked on by several Claude Code sessions at once, each running
in its own terminal, each with a narrow area of responsibility. This file is
the thing every one of them reads first — and it stays small on purpose: it
holds rules, not a directory of who's who.

Instead:

> **On startup: list `agents/*/AGENT.md` and read every one of them.** That's
> always current, because it's the actual thing, not a summary of it. Do this
> before doing anything else, every session, not just the first time —
> another agent's scope may have changed since you last looked.

Then read your own `agents/<slug>/AGENT.md` again, properly, and check your
own `agents/<slug>/mailbox/`.

**There is no mailbox for the manager** — reaching him is not the same as reaching another agent. Two different tools, for two different urgencies:

- **Needs his attention or a decision now** (blocked, found something
  urgent, a real question standing between you and continuing): call the
  `PushNotification` tool yourself, directly. It's a real interruption —
  a terminal/phone alert — so don't reach for it for routine progress; use
  it the way its own description says to.
- **Worth knowing, nothing urgent** (finished a task, changed something,
  general status): write it to your own `agents/<slug>/STATUS.md` instead.
  He reads that when he checks in on you — no interruption, no file
  hidden in a mailbox he'd have no reason to open.

If you're unsure which one a given update calls for, that's exactly the
"scope unclear? ask" case below — a `PushNotification` asking which one he
wants is cheap; guessing wrong in either direction (silence on something
urgent, or noise on something routine) is the actual failure mode.

> **`agents/createagent.sh` is human-only. No agent may ever run it, for
> any reason, even if asked to by name.** Agent creation is a deliberate
> decision Raul makes and types the answers to himself — this is a
> safeguard against uncontrolled agent self-replication, not a formality.
> The script itself refuses to run without a real interactive terminal,
> which an agent's tool calls don't have — but don't rely on that alone;
> treat this as an absolute rule regardless of whether a workaround seems
> possible. If you think a new agent is needed, `PushNotification` the
> manager and ask him to run it himself. Never run it, never suggest he
> run it "so you can save him the typing," never construct a variant of it.

## What lives in `agents/<slug>/`

One folder per agent, and everything about that agent lives inside it —
nothing about any agent is scattered elsewhere in the repo:

- `AGENT.md` — who this agent is: role, goal, scope, explicit limits.
  Written once, updated rarely. Everyone can read everyone's — this,
  collectively, **is** the roster; there is no separate list of it.
- `STATUS.md` — what this agent is doing *right now* / just finished.
  Updated by the agent itself whenever something changes worth knowing.
  Everyone can read everyone's — check another agent's `STATUS.md` before
  asking them something it would already answer.
- `mailbox/` — this agent's mail.
  - `inbox/` — unread messages, one file each. Anyone can write here.
  - `read/` — where the agent moves a message once it's dealt with it.
    That move *is* the read-tracking — an empty `inbox/` means caught up,
    nothing fancier needed.
- `context/` — this agent's own private scratch space: future tasks it
  wants to remember, notes on a skill or quirk only it needs, anything not
  meant for anyone else. Not a mailbox — other agents shouldn't need to
  read another agent's `context/`, and shouldn't expect their own to be
  read by anyone else either.

## Protocol

1. **Start of session**: read this file, list and read every
   `agents/*/AGENT.md`, then check your own `agents/<slug>/mailbox/inbox/`.
2. **Stay in your lane.** If a task belongs in another agent's declared
   scope, mail them instead of doing it yourself — even if you technically
   could. They know the traps in their own area that you don't.
3. **Scope unclear? Ask the manager, don't guess.** `PushNotification` him
   and wait for an answer before proceeding on anything that isn't cleanly
   inside your own declared scope — this is worth the interruption; a
   wrong guess costs more of his time than a question does.
4. **Check with Warden before spinning up a pathmate browser.** Only one
   CDP session should ever be driving the live portal at a time — two
   agents clicking around it concurrently is how sessions get corrupted.
   Warden coordinates who's using it and when; ask first, every time, even
   if you're "just reading."
4b. **Kart keeps the shared repo synced, not everyone.** You all work out
    of the same checkout, so `wake_prompt.txt` has Kart run `git pull`
    first thing on every wake, before reading anything else. Don't also
    pull yourself out of habit — one agent doing it avoids the races and
    conflicts that come from seven doing it at once. If Kart's pull ever
    fails (conflicts, diverged history), that's a `PushNotification` to
    the manager, not something to force through.
5. **Set up a listener for your own mailbox, don't just poll it once.**
   Mail can matter enough to act on quickly. `inotifywait` is **not
   installed on this machine** — don't reach for it, the background
   process will just fail silently and you'll have no listener at all
   without realizing it. Use a plain poll loop instead, started as a
   background Bash command and watched with `Monitor` (only fires a
   notification when the count actually goes up, not every tick):

   ```
   prev=0
   while true; do
     n=$(find agents/<slug>/mailbox/inbox -maxdepth 1 -name '*.md' 2>/dev/null | wc -l)
     [ "$n" -gt "$prev" ] && echo "new mail: $n unread (was $prev)"
     prev=$n
     sleep 60
   done
   ```

   The point is you find out within about a minute, not only when you
   happen to next check.
6. **Mail briefly, and manage your inbox actively — it pollutes your
   context if you let it pile up.** A few sentences per message; link to a
   file, commit, or artifact for detail rather than pasting large content
   in. Read a message, act on it (or note it in your own `context/`), move
   it to `read/`. Don't leave things sitting in `inbox/` unprocessed.
7. **Mail format**: filename starts with a timestamp,
   `YYMMDDHHMMSS_<name>.md`, followed by a name that actually describes
   the subject — not `update.md`. Body is markdown, not a text dump.
8. **Update Kart with your progress**: what you finished, and what you
   expect to deliver in your next stretch of work. Sanity-check that what
   you're about to take on still actually fits your declared scope before
   you tell him you're doing it — if it doesn't, that's the manager's call,
   not something to quietly stretch into.
9. **Identify yourself.** Open your session by stating your codename and
   role plainly (e.g. "Loom — r_ groups automation") so the manager can
   tell terminals apart at a glance.
10. **Keep your console tab labeled with your codename.** `wake.sh` sets
    this automatically when it opens your terminal. If you ever notice it's
    reverted (e.g. to `bash` or a working directory), reset it yourself:
    `printf '\033]0;<Codename>\007'`. The point is the manager can tell
    terminals apart by glancing at the tab bar, without opening any of them.
    For the same reason, `wake.sh` also launches you with
    `--remote-control <Codename>` so you're reachable from the manager's
    other devices by default — nothing you need to do about this yourself.
11. **You may be cut off with as little as ~10 minutes' notice.** Don't let
    anything important exist only in this conversation. Write progress,
    in-flight state, and next steps to your own `agents/<slug>/context/`
    (or `STATUS.md`, if it's something another agent or the manager should
    see) continuously, as you go — not as a last-minute dump you might not
    get time to do. Keep `context/` itself tidy: prune notes that are no
    longer relevant instead of letting it grow into a dump you'd have to
    re-read in full next time.

## PMCP documentation: check it first

Official PMCP v6.0 docs: https://my.pathmate.app/pmcp-documentation/doc-6-0
(public, readable with `WebFetch`, no browser slot needed). Before you
infer how PMCP behaves (rule semantics, variables, micro dialogs, timing),
search here first, and cite the page when you rely on it. Useful entry
points: `.../sections/coachings/variables`, `.../sections/coachings/rules`,
`.../sections/coachings/micro-dialogs`, `.../best-practices/timing-messages`.

## Tools

- `agents/createagent.sh` — interactive scaffold for a new agent (human-only,
  see above): asks for a slug, codename, and description, creates its whole
  `agents/<slug>/` folder (`AGENT.md`, `STATUS.md`, `mailbox/`, `context/`)
  in one shot. Nothing else needs updating anywhere else when a new agent
  is created — that's the point.
- `agents/mail.sh <to> "<subject>" ["<body>"]` — send a message, named and
  timestamped per rule 7 automatically. Without a body argument, reads the
  body from stdin. Written to `agents/<to>/mailbox/inbox/`.
- `agents/checkmail.sh [slug]` — list unread mail for `slug` (default: your
  own, via `$AGENT_SLUG`). Pass `--read FILE` to print one message and
  move it to `read/`.

**`AGENT_SLUG` is already set for you** — `wake.sh` launches your session
as `AGENT_SLUG=<slug> claude ...`, so it's part of your process environment
from the start and every `Bash` tool call inherits it automatically.
**Don't `export` it yourself** — it's already there (`echo $AGENT_SLUG` to
check), re-exporting it is a no-op at best, and it isn't on the allow-list
so it'll stop and ask Raul to approve a permission prompt for nothing. If
`echo $AGENT_SLUG` ever comes back genuinely empty, that's a real problem
(you weren't launched correctly) — `PushNotification` the manager rather
than papering over it with your own `export`.

## A note on scope for all agents

Every one of you was set up with a starting description, not a finished
spec — the manager expects to refine your actual boundaries as real tasks
come up. When in doubt about whether something is yours to do, that's not
a failure state, it's the expected case: ask.
