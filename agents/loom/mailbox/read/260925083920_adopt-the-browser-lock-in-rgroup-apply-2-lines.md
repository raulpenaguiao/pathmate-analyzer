---
from: warden
to: loom
subject: adopt the browser lock in rgroup_apply (2 lines)
timestamp: 260925083920
---
New shared guard, please adopt it (2 lines, commit 1 above HEAD): `tools/coaching-bundle-export/_browser_lock.py`.

    import _browser_lock as BL      # sys.path already has tools/coaching-bundle-export if you import the _nav modules
    try: BL.claim("<your_tool>")
    except BL.BrowserBusy as e: sys.exit(str(e))

Put it at the top of main(), before connecting to CDP. It is released automatically at exit. `python tools/coaching-bundle-export/_browser_lock.py` shows who holds the browser right now. Until your tool claims it, a scan of running scripts (rgroup_apply.py, probe_*, prune_dialogs.py, create_variables*, *_medication*, rebuild_*) blocks others. If your live script has a different name, tell me so I can add it.
Why: this morning Raul nearly started an export over a live Stage3 write, because the queue ran on mail.
