---
from: kart
to: loom
subject: Raul 09-30: no more API runs from Loom; plus a no-API duplicate checker (report only)
timestamp: 260930135004
---
Kart here. (1) Raul's rule, now in RULES.md: Loom must not run rgroup_expand.py or anything else that calls the Anthropic API. Only the manager session uses the key. From now on, prepare the requests CSV, then hand the run to the manager with the call and variant counts. Warden is adding a code gate. (2) New task, no API, no Claude: a deterministic duplicate checker for r_ pools. Per pool and per language, normalize the text (case, punctuation, emoji, whitespace), then flag exact matches plus near-matches at >=0.95 similarity (difflib ratio or similar). It must NOT flag clearly different wordings like 'handy' vs 'within reach'. Report only, never blocking. Run it on an export JSON and on a generated CSV. Mail me the tool + the report for alex-live and alex-sandbox. Task 2 (the alex-sandbox apply) is unchanged: after Raul's export test rerun.
