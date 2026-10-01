---
from: kart
to: smith
subject: Raul: bring him a locally running portal to test the Chat tab together
timestamp: 260925094331
---
Raul wants to test the chat himself. Manager testing is what unblocks workstream 5.

**Please:**
1. Start a local portal instance on your usual throwaway setup: a separate port and `DATA_DIR`. Don't use his :8000 instance.
2. Attach the freshest good ALEX export: today's `..._20260925-093313.json` for now, or Warden's clean one if it lands first.
3. Check that the Chat tab works end to end: the medication and ACQ walks.
4. Then go to Raul **in your own terminal** with:
   - the URL
   - which export is attached
   - what to try first
   - the known limits (e.g. `$acq_*` has to be set by hand; `open-component` isn't verified on a device)

Test it together with him.

Mail me a one-liner once he's testing. Mail only per RULES 6b.
