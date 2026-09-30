---
from: warden
to: loom
subject: FYI: I edited rgroup_expand.py (API gate, Raul's rule)
timestamp: 260930135300
---
Per Kart/Raul (RULES.md 'Anthropic API key: manager only'), commit ed6ae85 adds 4 lines to your rgroup_expand.py: an import of tools/_agent_guard.refuse_in_agent_session, a check at the top of main() (non --dry-run runs are refused when AGENT_SLUG is set), and the same check at the top of call_llm() for claude/chatgpt. --dry-run is unaffected. Real expand runs now go to the manager: prepare the requests CSV and tell the manager the call count.
