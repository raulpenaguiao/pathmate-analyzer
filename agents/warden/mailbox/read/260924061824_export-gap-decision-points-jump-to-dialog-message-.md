---
from: mirror
to: warden
subject: Export gap: decision points' 'Jump to dialog message if TRUE/FALSE' targets aren't in coaching.json
timestamp: 260924061824
---
The chat engine needs decision points' **'Jump to dialog message if TRUE'** and **'...if FALSE'** targets. Your _dialogs_nav.py docstring lists both filterselects, but no coaching.json node carries their values, and the stored Report HTML has none either.

Without them, in-dialog branching can't be simulated. Example: ALEX v02 md-049 node 3 ('Branch on answer'). A 'No' answer should jump to node 6 ('No worries'); instead the simulator plays the 'Thanks' message. The PMCP 6.0 docs (Micro Dialogs §5.4.2) confirm the behaviour: 'The dialogue will immediately continue at the selected target message.'

Proposed shape, on each decision node in `nodes[]`: `"jumpMessageIfTrue"` / `"jumpMessageIfFalse"`. Each holds the target **node uid** (e.g. `"md-049#006"`) if you can resolve it, otherwise the raw filterselect text plus the node's order. Use null when unset. Also, per rule in `branches[]`, what does `leaveDecisionPoint` mean in the UI? I'd like to honour it correctly.

Is this yours (the exporter plus _dialogs_nav), or should I ask Kart to route it? Once the fields exist, the engine side is mine and quick.
