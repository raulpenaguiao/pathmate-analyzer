# Channels and Media

Index: https://my.pathmate.app/pmcp-documentation/doc-6-0/communication-channel · fetched 2026-09-29 · condensed extracts, one section per subpage

## Push Notification ("reminders")
https://my.pathmate.app/pmcp-documentation/doc-6-0/communication-channel/push-notification

Three kinds:
1. **App-generated** (coded in the app, e.g. medication reminders set in the app menu). These can't be configured in the editor.
2. **Pushes for new chat messages:** automatic when the bot sends a message while the user is offline, showing the first words.
   - **Smart (default):** "no notification will be sent if another push was sent within the last 6 hours".
   - **Forced:** on the first message → *Show additional settings* → *This message is always announced by a push notification*.
3. **Intervention-generated push only:** *This message is ONLY a push notification and NOT appears in the chat*. "The notification is sent as a push notification only and does not appear in the chat." Example: remind to complete a questionnaire "after X hours of inactivity".

## Push Notifications (delivery)
https://my.pathmate.app/pmcp-documentation/doc-6-0/communication-channel/push-notifications

- Delivery goes via APNs/FCM with a device token, at maximum priority. "Whether a notification is ultimately delivered is determined solely by Apple or Google — not by MobileCoach."
- Per-message settings: default (the system decides) / ONLY push / ALWAYS announced.
- Default sequence when the user is outside the app: the 1st bubble pushes its text plus a badge; the 2nd pushes "..."; later bubbles increment the badge. "ALWAYS announced" bubbles show their real text.
- **Why delivery fails:** TestFlight (not guaranteed), permission not granted (asked at the end of screening), user-disabled, Android manufacturer battery/privacy tools, badge fragmentation, low battery.

**Pile-up relevance (ours):** with smart pushes (6 h), a re-ask or re-entry opener may arrive with no push at all. Consider *always announced* on re-entry openers of rank-1 reminders.

## Questionnaires
https://my.pathmate.app/pmcp-documentation/doc-6-0/communication-channel/questionnaires

- Built in PMCMS (no JSON editing). Config: `id`, `version`, `title`, `complete`, `teaser`, `mode` (Page/Default), `shufflePages`, `description`, `cover`, **`validDays`** (how long it stays accessible), `multiSubmit`, `resetValues`, `WriteToVariables`.
- Elements: Image, Text, Stage Text (bullets), Slider, Text Input, Select-One/Many, with conditions on earlier answers.
- **Variables:** questionnaire variables are local. "Values stored in Questionnaire variables are not automatically transferred to coaching variables". You need explicit bindings under *Manage dynamic variables and bindings*, and the target coaching variables must have Access = "Manageable by Service".
- **Triggering from chat:**
  - Option 1, a chat button: message 1 `questionnaire <Coaching Reference ID>`; message 2 `open-component:questionnaire` + newline + `<Questionnaire ID>:<Button Title>`. The questionnaire **blocks the chat until completion**. Needs the "chat only" feature.
  - Option 2, the overview list only: just the `questionnaire <ref>` command. Good for parallel questionnaires.
- The overview shows it according to the trigger time, `chatOnly` and `validDays`. No reminder mechanism is documented.

## Emails
https://my.pathmate.app/pmcp-documentation/doc-6-0/communication-channel/emails

The address goes in `$participantDialogOptionEmailData` (user) or `$participantSupervisorDialogOptionEmailData` (supervisor). Message text: first line = subject, the rest = body. *Show additional settings* → *Channel to use for message sending* = Email to participant / Email to supervisor. Header and footer are set in Basic Settings. Uses: re-engagement, an alternative channel, supervisor inactivity alerts.

## Commands
https://my.pathmate.app/pmcp-documentation/doc-6-0/communication-channel/commands

Commands in messages run on delivery; **unknown commands fail silently**. Syntax `command arg1 arg2`.
- **Display:** `show-link <url> <title>`, `show-universal-link {button,url,data?,confirmationDialogue?}`, `show-web <url> <title>` (in-app), `show-info <id>` (open/close tracked), `media-library-button <id> <title>`, `navigate <screen>`, **`wait <seconds>`** (pacing).
- **Features:** `activate-dashboard-chat`, `show-local-info <id>`, `service-channel-news {id,category,title,text?,button?,url?,button2?,url2?,deleted?}` (the same id updates the entry).
- **Settings:** `settings <name> <value>`, `request-push-permissions`.
- **Tasks:** `add-task {id,title,intervalType daily|selected_days|single_time,iterationTimes,iterationDays,reminderActive,startingTime}`, `remove-task <id>`.
- **Gamification:** `increment-achievement <id> <value>`.
- **Media library:** `add-media-library`, `unlock-media-library`, `save-as-favorite`, `set-media-library-tags`. Questionnaire: see above.

## Media Library
https://my.pathmate.app/pmcp-documentation/doc-6-0/communication-channel/media-library

A persistent in-app collection (video files or Vimeo, audio, links, info cards). It needs a PCMS screen with id `media-library`.
- **Commands:** `add-media-library {…}` (store in the background), `show-media-library {…}` (show and store), `unlock-media-library ID`, `media-library-button ID [title]`, batch forms `add-/show-media-library-items {"items":[…]}`, and `set-media-library-tags`.
- **Size limits:** images 5 MB, audio 50 MB, video 100 MB (H.264).

## JSON Service Channel News
https://my.pathmate.app/pmcp-documentation/doc-6-0/communication-channel/json-service-channel-news

In-app news (the mail icon). Create it as a micro-dialogue **Event** (+New Event), with channels under Events & Actions → New Coaching Event Group. JSON: `{id, category, title, text, button, url, deleted, popup}`. Target it with rules (e.g. `$XY text value equals 1`). Images are 800×450. Activate with Switch Status, and deactivate before editing.

## Infocards
https://my.pathmate.app/pmcp-documentation/doc-6-0/communication-channel/infocards

Markdown snippets with `<meta title="…" subtitle="…" />` and an optional `<button>…</button>`. Images are `![alt](hash)` from the Media Library. Show one with a command message `show-local-info ID` (tick "This message is a command").

## Media Objects · Editing Pictures
https://my.pathmate.app/pmcp-documentation/doc-6-0/communication-channel/media-objects · https://my.pathmate.app/pmcp-documentation/doc-6-0/communication-channel/editing-pictures

Media go in chat messages or infocards. Images are at most 1500×2000 (never enlarged); use JPG for photos and PNG for graphics. SCN and questionnaire images are 800×450. There's also a GIMP/ImageOptim workflow.

## Apple Health & Google Health Connect
https://my.pathmate.app/pmcp-documentation/doc-6-0/communication-channel/apple-health-google-health-connect

Step counts arrive in `$stepsHealthIos` / `$stepsHealthAndroid` (the daily total, at the data point's timestamp). Sync runs about every 30 min in the background; there's none in the foreground or when the app is closed. Start with `start-background-health-tracking $participantIdentifier $sensing_pmHealthSecret` and stop with `stop-background-health-tracking`. "There is currently no detection of a lost connection to the Health app." Needs Android 12+ or iOS 15+.

---

Note (ours): **no command deactivates, recalls or clears open questions.** In ALEX those are message settings in the editor ("Deactivates and remembers all former open questions", "Recalls former deactivated questions from last deactivation", "clears the current dialog cascade"), and none of them is documented.
