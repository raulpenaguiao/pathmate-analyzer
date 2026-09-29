# JavaScript Snippet (and MCP Client Integration)

Sources, fetched 2026-09-29, condensed extracts:
- https://my.pathmate.app/pmcp-documentation/doc-6-0/sections/coachings/javascript-snippet
- https://my.pathmate.app/pmcp-documentation/doc-6-0/sections/coachings/mcp-client-integration ("Last Updated: June 2026")

## Setup
In a decision point: New rule → **"Execute javascript in x and store values but result is always true"** → **"Edit Rules [x] (with placeholders)"**.

## Execution
1. **Placeholder substitution before parsing:** `$var` → value as text; `$$objectName$$` → a full JSON object; `$$storyProgress$$` (all questionnaires and answers, latest at `[0]`) and system variables are injected.
2. Runs as **ECMAScript 2024**.
3. The **last expression must be an object literal**. Each key is written as a participant variable.
4. The rule is always TRUE; the flow continues immediately.
- **60 s hard timeout**, with no partial results.

## Rules
- Input and output variables must exist, with the access setting **"manageable by service"**.
- Quote text variables: `'$weightKg' * 1`. **Missing variables become empty strings**, not undefined, so guard with `'$x' || 'default'`.
- Output types: null/undefined → `"null"`; booleans → `"true"`/`"false"`; numbers via `toString()` (integers stay `84`); arrays and objects → JSON.
- `import` lines are stripped (kept for IDE use).

## Libraries (`//+ moment, fetch, mcp, file-data, llm`)
`moment` 2.30.1 · `fetch(url, opts)` · `mcp(...)` · `fileData(...)` (media store) · `llm(index, prompt)` · `pm-json-compress-light`. **All helpers are synchronous**; top-level `await` and async root functions aren't supported.

## Sensor data
```js
const hr = { "$$SENSOR_DATA$$": "heartrate", "types": ["bpm","rest"],
             "startRelativeInclusive": "-7d", "endRelativeExclusive": "now" }
```
Elements are `{timestamp(ms), type, data(string)}`. You can also use `startTimestampInclusive`/`endTimestampExclusive`. **Queries are static**, substituted before parsing, so they can't be built from JS variables.

## Debugging
Use a `DEBUG` flag to swap placeholders for fixtures. Return `debug_…` keys and inspect them in the admin UI.

## Pitfalls
The result object must be last; quote string placeholders; mind the 60 s timeout; files are kept only if their reference is in the result object.

## MCP client (needs custom activation: project-support@pathmate.app)
`mcp(serverUrl, method ('tools/call'|'tools/list'), params, requestId?, {headers, trustAllCerts}?)` returns `{status, success, result, error, response, rawResponseBody}`. Timeouts: 10 s connect, 30 s read. `file:<ref>` params are loaded from the media store and base64-encoded. Typical async pattern: request → job id in a variable → poll → download → store the file reference → show it.
`llm(index 1–5, systemPrompt?, prompt)` returns `{success, message, error}`.

**Relevance (ours):** JS rules could do calendar-exact expiry, per-topic counters or queue logic in one block. Whether a JS rule sees variables written earlier in the same PERIODIC pass is not documented (same as for normal rules).
