# Agent rules

This repo is worked on by several Claude Code sessions at once, each running
in its own terminal, each with a narrow area of responsibility. This file is
the thing every one of them reads first — and it stays small on purpose: it
holds rules, not a directory of who's who. **Who exists and what they do is
never written down here** — that would just go stale the moment someone's
scope changes or a new agent shows up, and then everyone's working from a
copy that's wrong in a way nobody notices until it causes a mistake. Instead:

> **On startup: list `agents/*/AGENT.md` and read every one of them.** That's
> always current, because it's the actual thing, not a summary of it. Do this
> before doing anything else, every session, not just the first time —
> another agent's scope may have changed since you last looked.

Then read your own `agents/<slug>/AGENT.md` again, properly, and check your
own `mailbox/<slug>/inbox/`.

The manager is Raul. **There is no `mailbox/manager/`** — a file he'd have
to remember to go open isn't a notification, and reaching him is not the
same problem as reaching another agent. Two different tools, for two
different urgencies:

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

## The three folders

- **`agents/<slug>/`** — one folder per agent.
  - `AGENT.md` — who this agent is: role, goal, scope, explicit limits.
    Written once, updated rarely. Everyone can read everyone's — this,
    collectively, **is** the roster; there is no separate list of it.
  - `STATUS.md` — what this agent is doing *right now* / just finished.
    Updated by the agent itself whenever something changes worth knowing.
    Everyone can read everyone's — check another agent's `STATUS.md` before
    asking them something it would already answer.
- **`mailbox/<slug>/`** — this agent's mail.
  - `inbox/` — unread messages, one file each. Anyone can write here.
  - `read/` — where the agent moves a message once it's dealt with it.
    That move *is* the read-tracking — an empty `inbox/` means caught up,
    nothing fancier needed.
- **`context/<slug>/`** — an agent's own private scratch space: future
  tasks it wants to remember, notes on a skill or quirk only it needs,
  anything not meant for anyone else. Not a mailbox — other agents
  shouldn't need to read another agent's `context/`, and shouldn't expect
  their own to be read by anyone else either.

## Protocol

1. **Start of session**: read this file, list and read every
   `agents/*/AGENT.md`, then check your own `mailbox/<slug>/inbox/`.
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
5. **Set up a listener for your own mailbox, don't just poll it once.**
   Mail can matter enough to act on quickly. A `Monitor` on something like
   `inotifywait -m mailbox/<slug>/inbox` (one event per new file) is one
   concrete way to do this — the point is you find out promptly, not only
   when you happen to next check.
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

## Tools

- `agents/createagent.sh` — interactive scaffold for a new agent (human-only,
  see above): asks for a slug, codename, and description, creates its
  `agents/`, `mailbox/`, and `context/` folders. Nothing else needs
  updating anywhere else when a new agent is created — that's the point.
- `agents/mail.sh <to> "<subject>" ["<body>"]` — send a message, named and
  timestamped per rule 7 automatically. Without a body argument, reads the
  body from stdin. Written to `mailbox/<to>/inbox/`.
- `agents/checkmail.sh [slug]` — list unread mail for `slug` (default: your
  own, via `$AGENT_SLUG`). Pass `--read FILE` to print one message and
  move it to `read/`.

**Set `export AGENT_SLUG=<your-slug>` at the start of your session** —
`mail.sh` signs outgoing mail with it and uses it to default `checkmail.sh`.
Without it, mail still sends, it just gets signed with your unix username
instead of your slug, which makes it harder for whoever receives it to know
who to reply to.

## A note on scope for all agents

Every one of you was set up with a starting description, not a finished
spec — the manager expects to refine your actual boundaries as real tasks
come up. When in doubt about whether something is yours to do, that's not
a failure state, it's the expected case: ask.
