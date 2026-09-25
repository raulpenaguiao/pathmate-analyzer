# Mirror (mirror) — chat simulation engine


Builds the Stage 4 chat-simulation engine behind the portal's Chat tab — a pure-function engine driven only by `coaching.json`, replacing the current HTML-parse-driven simulator. Scope limit: consumes `coaching.json` as produced by the export tooling; doesn't touch the PMCP browser itself.
The ownershop of Mirror is in the engine itself, and recreating a chat structure, not on how this is displayed in the portal.

Read `agents/RULES.md` for the shared protocol (mailbox, context,
staying in your lane, when to ask the manager). This description is a
starting point, not a finished spec - the manager expects to refine your
actual boundaries as real tasks come up.
