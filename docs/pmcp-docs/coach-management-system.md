# Coach Management System (PCMS)

Fetched 2026-09-29 · condensed extracts

## Overview
https://my.pathmate.app/pmcp-documentation/doc-6-0/coach-management-system

The PCMS configures a whole MobileCoach project. It has 13 tabs:
- Home
- **App**: development QR (test environment) and production QR (live)
- Basics: app name, logo, languages including Romanian, language order
- Coach: coach names and images, one per tab
- Colors: with a live preview
- Onboarding texts
- Screens
- Questionnaires: used via commands in the editor
- Media Resources: images up to 5 MB JPEG/PNG; audio up to 50 MB AAC/M4A; video up to 100 MB MP4/M4V H264; each gets a unique ID
- Coaching: link to the editor
- Data Export
- **Transfer**: export/import the complete configuration for backups or reuse across environments
- Account

## App Screens
https://my.pathmate.app/pmcp-documentation/doc-6-0/coach-management-system/app-screens

- **Custom screens** have an id, an icon, a localised title and a menu-visibility option. **Overwritable defaults:** `account`, `privacy-policy`, `more`, `legal`, `security`, `daily-plan`, `media-library`.
- **Content** is a JSON array of elements: `md`, `collapsable_md_block`, `screen_button` (`screenId`), and image buttons (layout small/medium/large; mode cover/contain/stretch).
- **Variables in screens** need **Autosync** set in the editor.
- **Conditions:** an element shows when its server variable is not undefined, null, empty or 0.
- **Buttons** trigger `$participantIntention`. Handle them with an "Execution on USER INTENTION" rule and `text value equals`.
- **Daily Plan module:** medication reminders, goals and tasks, managed with `add-task` / `remove-task` (properties: `id`, `title`, `startingTime` (unix), `iterationTimes` or `["ANY"]`, `reminderActive`, `intervalType` daily/selected_days/single_time, `iterationDays` MON…SUN).

## Adherence Cockpit
https://my.pathmate.app/pmcp-documentation/doc-6-0/coach-management-system/adherence-cockpit

- **Adherence** = "whether users follow the intended coaching program", configured per coaching. There are two types: **IC** (intervention components) and **HPB** (health-promoting behaviours).
- **Setup:** (1) components, (2) coaching plan, (3) thresholds.
- **Component fields:** Name, Type IC/HPB, **Target** (fixed or a variable), **Actuality** (the variable with the achieved value), **Period** (a `$periodId` integer that increments by 1), Units. "The period MUST BE incremented by 1 **BEFORE** the actual measurement (Actuality) is reset."
- **Calculation:** when a period ends, actuality/target gives the adherence; then the period is incremented and the actuality reset. Periods can start at any time and vary in length. The **main period** should be at least as long as the component periods.
- **`$adherenceActive`:** the user is included while the value is not undefined, null, false or 0 (for pauses, inactive phases and so on).
- **Plan:** groups combine components with AND, with weights (e.g. reflection 70% / exercise 30%). Groups are OR'd together.
- **Thresholds**, e.g. adherent: above 75%; at risk: below 30% for 2 consecutive periods.
- **Dashboard:** aggregated, per component, per user (at-risk list, export). Syncs nightly; there are "Refresh adherence definition" (1–2 min) and "Refresh data" buttons.

**Relevance (ours):** this is a built-in adherence model. The variables proposed in `docs/participant_data_collection.md` (done/ignored counters per topic) could feed it directly as Actuality and Period variables.
