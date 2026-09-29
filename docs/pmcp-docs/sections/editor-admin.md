# Coaching Editor: overview, Coachings list, Access Control, Account · Translations

Fetched 2026-09-29 · condensed extracts

## Coaching Editor overview
https://my.pathmate.app/pmcp-documentation/doc-6-0/sections

Left menu: Home, Coachings, Events & Actions, Access Control, Account, Documentation.

## Coachings list
https://my.pathmate.app/pmcp-documentation/doc-6-0/sections/coachings

- **New**, **Edit**, **Duplicate** ("especially useful when you want to create a similar coaching without starting from scratch"), **Export/Import** (backups, moving between servers), **Rename**.
- **Delete:** "You can only delete a coaching, when the Monitoring Status and the Coaching Status are set to 'inactive'".
- **Validate:** checks for "typical errors or inconsistencies". The Validation Report covers six categories, e.g. empty selection prompts, formatting, spacing, command inconsistencies across languages.
- **Report:** HTML documentation of all messages and rules. This is what our export tooling reads. (See memory: the Report omits the Randomisation Group column.)
- **Results**, **Internationalisation**, **Problems** (detected issues plus solutions), **Support** (reset monitoring, manage participant accounts), **Brand** (JSON branding variables).

## Access Control
https://my.pathmate.app/pmcp-documentation/doc-6-0/sections/access-control

| Role | Can | Concurrency |
|---|---|---|
| Global Admin | everything | **max 1 per coaching** |
| Global Author | content across coachings, can't create coachings | many |
| Coaching Admin | edit its coaching, manage its users and data | **max 1 per coaching** |
| Coaching Author | edit the assigned coaching only | many |
| Team Manager | participant dashboard, limited data | external supervisors |

Functions: New, Set Team, email/language/password updates, reset 2FA, delete, *Make …* role buttons. One person may hold several accounts (e.g. admin + author).

## Account
https://my.pathmate.app/pmcp-documentation/doc-6-0/sections/account

Set password; Recreate / Show 2FA secret; **Reset All Locks** logs out users stuck in a coaching session (e.g. after the browser closed). Warn colleagues first to avoid data loss.

Relevance (ours): the one-admin-per-coaching lock is why Warden serialises browser sessions. "Reset All Locks" is the documented escape hatch for a stale lock.

## Translations
https://my.pathmate.app/pmcp-documentation/doc-6-0/translations · …/translations/chat-dialogues · …/translations/store-descriptions · …/translations/faqs

- **The coaching must be deactivated** (monitoring and coaching status inactive) before exporting.
- **Internationalisation** → Export *Messages & Dialogs* (all messages and answer options), *Coaching Variables*, *Surveys & Feedbacks*. A "Minimal export timestamp" gives incremental exports.
- Translate in a spreadsheet. **Don't touch** the Identifier/Description columns (A–B) or the original text (C–D), and don't change the row or column structure. Keep spaces and line breaks. Never translate commands or variables. Keep emojis. Convert .xlsx back to CSV before re-importing.
- Re-import via *Import Messages & Dialogs* / *Import Coaching Variables*.
- The Store Descriptions and FAQs pages had no body content when fetched (navigation only).

Relevance (ours): this is a documented bulk path for message text, an alternative to the Playwright row-by-row edits for r_ content (Loom). But it needs the coaching deactivated.
