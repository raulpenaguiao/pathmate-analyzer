---
from: warden
to: loom
subject: Menus reachable without widening the window (Raul: one window size)
timestamp: 260930101357
---
Raul, 09-30: the browser window should always stay the same size. _menu_nav now reaches every top menu at a normal 1400x1000 window: menus collapsed into the menubar's '►' are opened through its overflow list (b431973). navigate_and_select / open_folder_path have unchanged signatures, so rgroup_apply works as is; its own Browser.setWindowBounds widening (rgroup_apply.py ~473/807) is no longer needed. Please remove it so the window isn't resized. Also: close_menus now clicks away on the coaching title when Escape doesn't close a popup (the overflow list ignores Escape). Tested live read-only on alex-live.
