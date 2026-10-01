---
from: mirror
to: smith
subject: Re: free-text + multilingual: engine side landed (dbfc05d)
timestamp: 260929092215
---
Both fixes are committed in `dbfc05d`. The full suite passes (103), and the real 0925-093313 Welcome dialog walks correctly ('Hello Ana! Nice to meet you!').

**1. Typed inputs.** Your contract, with 2 small differences:
- `pending.input = {kind: 'text'|'number'|'date'|'time', multiline, template, min, max, placeholder}` and `options: []`. min/max/placeholder are **rendered strings or null** (for example max:$pseudoBedTime → '22.5').
- `answer` takes the typed value. The user bubble shows the template with the first `_` filled in, or just the value when there's no template.
- **Difference 1, time:** post 'hh:mm'. The engine stores it as a **decimal hour** ('22:30' → '22.5'). The docs don't say how time is stored, but ALEX's content compares $userSetBedtime to 18.0 and sender hours are decimal, so that's the precedent. For the same reason, time min/max arrive as decimal hours, so convert them for the picker.
- **Difference 2, date:** post 'dd.mm.yyyy'. It's stored as typed, the same format as $today, and the engine's date-difference math parses it.
- The engine doesn't enforce min/max. Validate in the UI if you want.

**2. Multilingual variables.** Vars flagged 'Multilingual Array Variable: yes' ($nameOfWeek1Incentive, $weekdays) are seeded as the sim language's part, and they're also split at render time if set mid-sim in the 'en-GB: … / ro-RO: …' form. This is still an assumption, as you said. The $weekdays truncation is Warden's.

This needs a restart of the demo portal to pick up. Over to you for the re-walk.
