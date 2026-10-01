# 24 Message editor (scrolled to the bottom)

![Message editor (scrolled to the bottom)](24-message-editor-bottom.png)

alex-sandbox, captured by doc_screens.py. Same editor as 22, scrolled down.

Blue numbers label each control; **red boxes** mark controls whose meaning is unknown.

| # | control | caption | greyed out | open question |
|---|---|---|---|---|
| 1 | button | Upload |  |  |
| 2 | button | Delete | yes |  |
| 3 | label | (no value set) |  |  |
| 4 | button | Edit |  |  |
| 5 | label | Media object title: |  |  |
| 6 | filterselect | (dropdown) |  |  |
| 7 | label | Linked intermediate survey: |  |  |
| 8 | label | (no value set) |  |  |
| 9 | button | Edit |  |  |
| 10 | label | Message key (must not be unique): |  |  |
| 11 | label | (no value set) |  |  |
| 12 | button | Edit |  |  |
| 13 | label | Randomisation group: |  |  |
| 14 | checkbox | This message is a command (invisible for participant) |  |  |
| 15 | checkbox | This message expects to be answered by the participant |  |  |
| 16 | filterselect | custom |  |  |
| 17 | label | Answer type: |  |  |
| 18 | label | en-GB: open-component:questionnaire OnInfoCard_15-19_1:Open Quiz / ro-RO: open-component:questionnaire OnInfoCard_15-19_1:Chestionar deschis |  |  |
| 19 | button | Edit |  |  |
| 20 | label | Answer options (with placeholders): |  |  |
| 21 | label | (no value set) |  |  |
| 22 | button | Edit |  |  |
| 23 | label | Store message reply to variable (if required): |  |  |
| 24 | label | (no value set) |  |  |
| 25 | button | Edit |  |  |
| 26 | label | Store the following value in case of no reply (if required): |  |  |
| 27 | checkbox | Show additional settings |  |  |
| 28 | label | Channel to use for message sending: |  |  |
| 29 | filterselect | 👤 App/partner message to participant |  |  |
| 30 | checkbox | This message’s answer can be cancelled (NO value will be set on cancel) |  | What does 'cancel' mean for the participant (no value is set)? |
| 31 | checkbox | This message deactivates and remembers all former open questions | yes | Exact semantics of deactivating and remembering open questions? |
| 32 | checkbox | This message blocks the micro dialog until answered/unanswered |  | Exact blocking behaviour: until answered, or also until 'unanswered'? |
| 33 | checkbox | This message recalls former deactivated questions from last deactivation | yes | Which questions are recalled, from which deactivation? |
| 34 | checkbox | This message is sticky in the client |  | What does 'sticky in the client' mean? |
| 35 | checkbox | This message recalls former deactivated questions from most recent still filled deactivation | yes | What is a 'still filled' deactivation? |
| 36 | checkbox | This message is ONLY a push notification and NOT appears in the chat | yes |  |
| 37 | checkbox | This message clears the current dialog cascade (and remembered questions) | yes | What is a dialog cascade, and what does clearing it do? |
| 38 | checkbox | This message is ALWAYS announced by a push notification |  |  |
| 39 | checkbox | This message clears all dialog cascades (and remembered questions) | yes | Difference to clearing the current cascade? |
| 40 | checkbox | The cascade (and rem. quest.) of this message will not be cleared on clear all | yes | What is protected from 'clear all', and when does clear-all happen? |
| 41 | label | Minutes after sending until message is handled as unanswered: |  |  |
| 42 | button | 1 |  |  |
| 43 | button | 5 |  |  |
| 44 | button | 10 |  |  |
| 45 | button | 30 |  |  |
| 46 | button | 60 |  |  |
| 47 | button | infinite |  |  |
| 48 | caption | infinite |  |  |
| 49 | label | Message will only be send if the following rules are ALL TRUE: |  |  |
| 50 | column | Rule |  |  |
| 51 | button | New |  |  |
| 52 | button | Edit | yes |  |
| 53 | button | Move Up | yes |  |
| 54 | button | Move Down | yes |  |
| 55 | button | Delete | yes |  |
| 56 | button | Close |  |  |
