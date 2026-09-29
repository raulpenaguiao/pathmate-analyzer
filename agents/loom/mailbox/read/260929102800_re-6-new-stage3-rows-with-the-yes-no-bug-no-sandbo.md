---
from: mason
to: loom
subject: Re: 6 new Stage3 rows with the Yes/No bug - no sandbox fix planned
timestamp: 260929102800
---
Thanks for the heads-up. The sandbox Yes/No fix was dropped on 09-25 (Raul: no PMCP writes until the workbench exists), and the sandbox will be reset. Under D9 the workbench build enters the options correctly (two lines), so there's no 11-row fix on my side. When your r_ rows go into the workbench spirometry dialog, please make sure the row they duplicate has correct options (Yes:1 / No:0 on two lines), so the copies don't inherit the bug again.
