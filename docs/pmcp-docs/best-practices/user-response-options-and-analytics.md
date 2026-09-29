# User Response Options · Analytics

Fetched 2026-09-29 · condensed extracts

## User Response Options
https://my.pathmate.app/pmcp-documentation/doc-6-0/best-practices/user-response-options

1. **Real alternatives** on one continuous dimension (agree/disagree, interest/disinterest…). If both options could be chosen and still make sense, they aren't alternatives.
2. **Don't mix dimensions** in one set (e.g. "Sounds interesting." vs "I had the same experience.").
3. **Strength vs number of options:** a weak statement needs 1–2 options ("Okay, thank you."); a moderate one 2–3; a strong one 3 or more, to avoid reactance. Prefer softer wording ("I'd rather agree").
4. **Neutral/open options** ("I don't know", "Other reasons…", then free text only if the exact answer is needed).
5. **Balance the count:** more options give detailed insight and less reactance, but a higher cognitive load, more decision fatigue and more authoring effort.
6. **Single-option ("placebo") responses** keep a clear path and let the user set the pace. They must be neutral ("Okay!", "Let's continue.", "Can you explain it?"), not assertive ("That sounds great!"). Guideline: **no more than three consecutive coach messages without a chance to respond.**

## Analytics
https://my.pathmate.app/pmcp-documentation/doc-6-0/best-practices/analytics

Build an analytics list of every variable or measure needed for the KPIs and research questions.
- **Tracked automatically by the app:** DAU, WAU, session duration, frequency of use, retention rate.
- **Others you design:** engagement with specific content; ratings and NPS; goal completion; task completion time; milestones; feature usage; **drop-off points**; health metrics; demographics; **adherence to recommendations**.
- Table format: Measure | Description | Data Type | Frequency | Source | Relevant Variable(s), e.g. `$ratingUser`, `$goalCompleted`.

Relevant to `docs/participant_data_collection.md`: "adherence" and "drop-off" are named as measures, but the docs give no built-in logging of ignored prompts.
