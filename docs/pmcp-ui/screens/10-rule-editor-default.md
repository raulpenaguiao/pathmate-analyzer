# 10 Rule editor (sender rule, as is)

![Rule editor (sender rule, as is)](10-rule-editor-default.png)

alex-sandbox, captured by doc_screens.py. Rule: 🧐💬 If required, send feedback on poor compliance with lung function monitoring s

Blue numbers label each control; **red boxes** mark controls whose meaning is unknown.

| # | control | caption | greyed out | open question |
|---|---|---|---|---|
| 1 | caption | Comment: |  |  |
| 2 | label | 🧐💬 If required, send feedback on poor compliance with lung function monitoring scheme |  |  |
| 3 | button | Edit |  |  |
| 4 | caption | Rule [x] (with placeholders): |  |  |
| 5 | caption | Comparison term [y] (with placeholders): |  |  |
| 6 | label | $totalNumberOfConsecutiveDaysWithoutSpirometry |  |  |
| 7 | button | Edit |  |  |
| 8 | label | $hyperparameterToleranceForNumberOfConsecutiveDaysWithoutSpirometry |  |  |
| 9 | filterselect | calculated value is bigger than |  |  |
| 10 | label | Store rule result to variable (if required): |  |  |
| 11 | label | (no value set) |  |  |
| 12 | button | Edit |  |  |
| 13 | checkbox | Send message if rule result is TRUE |  |  |
| 14 | checkbox | Start micro dialog if rule result is TRUE |  |  |
| 15 | checkbox | Mark case as solved (unexpected message) and stop the current rule execution run if result is TRUE |  | What does 'mark case as solved' do, and where is a 'case' visible? |
| 16 | checkbox | Stop current rule execution run and finish coaching for this participant if rule result is TRUE |  | What happens to the participant when the coaching is finished by a rule? |
| 17 | filterselect | (dropdown) | yes |  |
| 18 | label | Message group to send messages from: | yes |  |
| 19 | filterselect | $participantNextMicroDialogIdentifier |  | Why is this variable shown even when 'start micro dialog' is unticked? |
| 20 | label | Micro dialog to start: |  |  |
| 21 | label | Hour to send message (24h hours, 0 = immediately): |  |  |
| 22 | caption | 00:00 | yes |  |
| 23 | filterselect | $userSetTimeOfTheDayForFeedbackIfRequired |  |  |
| 24 | label | Minutes after sending until message is handled as not answered: | yes | What happens when this time runs out (default 4 h)? Does it apply to dialog starts? |
| 25 | button | 1 | yes |  |
| 26 | button | 5 | yes |  |
| 27 | button | 10 | yes |  |
| 28 | button | 30 | yes |  |
| 29 | button | 60 | yes |  |
| 30 | caption | 0 days, 4 hours, 0 minutes | yes |  |
| 31 | tabsheet-tabitemcell | Rules if participant DOES answer | yes | When do 'does answer' rules apply? The tab stays disabled in every state we tried. |
| 32 | tabsheet-tabitemcell | Rules if participant DOES NOT answer | yes | When do 'does NOT answer' rules apply? The tab stays disabled in every state we tried. |
| 33 | label | Execute these rules if participant DOES answer to message: | yes | When do 'does answer' rules apply? The tab stays disabled in every state we tried. |
| 34 | label | Variable to store calculation result of selected rule: | yes |  |
| 35 | label | Send message after execution of selected rule: | yes |  |
| 36 | button | New | yes |  |
| 37 | button | Edit | yes |  |
| 38 | button | Expand | yes |  |
| 39 | button | Collapse | yes |  |
| 40 | button | Duplicate | yes |  |
| 41 | button | Delete | yes |  |
| 42 | button | Close |  |  |
