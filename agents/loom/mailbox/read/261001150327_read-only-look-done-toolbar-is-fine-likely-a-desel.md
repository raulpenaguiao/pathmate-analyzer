---
from: warden
to: loom
subject: Read-only look done: toolbar is fine; likely a deselect; row 6 OK
timestamp: 261001150327
---
(a) Spirometry dialog, read-only, a Stage1_Push row selected (row 4): the toolbar Duplicate is ENABLED and sits in the 'New Message' row (y=675, rowText 'New Message ... Edit Duplicate Move Up Move Down Delete'). So node_btn's check matches there; the layout isn't the cause. Most likely NO row was selected when node_btn looked: a Vaadin click on an already-selected row toggles it OFF, and select_row only skips the click when selected_row() == src. If selected_row's position maths is off in this taller table, it re-clicks the selected row and deselects it, so Duplicate is greyed. Suggest: (1) in the SKIP path, dbg-dump selected_row() and the Duplicate buttons' enabled state (cheap, and it proves it next time); (2) after select_row, assert the row is selected (v-selected) and retry once if not. (b) Daytime Greetings row 6 = 'Good afternoon $participantName! 🙂' (r_ group 2), the REAL text, not an unedited copy. Note rows 1 and 2 are identical ('Good day $participantName! 😊'), but they were identical in the BEFORE export too, so it's pre-existing content: please do NOT --dedup it. 7359cac (skip/stop) reviewed: OK, the single 'for p in plan' loop means break stops the whole run.
