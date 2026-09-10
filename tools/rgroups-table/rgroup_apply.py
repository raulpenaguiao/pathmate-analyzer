"""Step 4 of the r_ pipeline — rgroups_generated.csv -> the live PMCP editor.

Applies EVERY `ok` variant in ``rgroups_generated.csv`` (from
``rgroup_expand.py``) — there is no review gate. ``--limit N`` is REQUIRED
and caps how many variants are added. DEFAULT IS A DRY RUN; pass ``--apply``
to actually write. Needs a logged-in PMCP tab on the CDP browser
(``tools/start_pmcp.sh``).

  PMCP_CDP=http://127.0.0.1:9222 .venv/bin/python rgroup_apply.py --limit 5
  PMCP_CDP=http://127.0.0.1:9222 .venv/bin/python rgroup_apply.py \
      --apply --limit 1 --pool 'r_MorningGreetings @ Morning greetings'

Per variant (recipe mapped by
``../coaching-bundle-export/probe_add_message.py`` against the sandbox):

  1. navigate to the micro dialog (folder -> dialog in the Micro Dialogs menu)
  2. select an existing table row whose Randomisation Group == the target group
  3. **Duplicate** (node button, NOT "Duplicate Dialog") -> a copy is appended
     at the BOTTOM, keeping the group
  4. select the new bottom row -> **Edit** -> "Edit micro dialog message:" modal
  5. its **Edit** by "text (with placeholders):" -> "Edit text" sub-modal
  6. **English (GB)** tab -> replace the textarea with the en-GB text
  7. **Romanian (RO)** tab -> replace the textarea with the ro-RO text
  8. **OK** (commits the sub-editor) -> **Close** (outer modal)
  9. **Move Up** until the row directly above is in the same group

Idempotent: a variant whose en-GB already exists in the pool is skipped.

DEFAULT IS A DRY RUN - it navigates and prints the plan but performs no
mutating click. Pass ``--apply`` to actually write.

  PMCP_CDP=http://127.0.0.1:9222 .venv/bin/python apply_approved.py
  PMCP_CDP=http://127.0.0.1:9222 .venv/bin/python apply_approved.py \
      --apply --limit 1 --pool 'r_MorningGreetings @ Morning greetings'
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GENERATED = HERE / "rgroups_generated.csv"
CDP = os.environ.get("PMCP_CDP", "http://127.0.0.1:9222")


def menu_path(meta_row) -> list[str]:
    fp = (meta_row["folderPath"] or "").strip()
    segs = [s.strip() for s in fp.split(" / ") if s.strip()] if fp else []
    return segs + [meta_row["microDialog"]]


def build_plan(args):
    """Read rgroups_generated.csv (from rgroup_expand.py) and turn every `ok`
    variant into a plan item. No review gate — everything generated is
    applied; `--limit` caps the count."""
    if not GENERATED.is_file():
        sys.exit(f"{GENERATED.name} not found — run rgroup_expand.py first")
    rows = list(csv.DictReader(GENERATED.open(encoding="utf-8")))
    meta = {}
    plan = []
    for r in rows:
        pool = r["pool"]
        meta.setdefault(pool, {
            "group": r["randomisationGroup"], "microDialog": r["microDialog"],
            "folderPath": r["folderPath"], "existing_en": set()})
        if args.pool and pool != args.pool:
            continue
        en, ro = (r.get("en-GB") or "").strip(), (r.get("ro-RO") or "").strip()
        if r.get("status") != "ok" or not en:
            continue
        plan.append({"pool": pool, "en": en, "ro": ro,
                     "group": r["randomisationGroup"],
                     "path": menu_path(r), "skip_existing": False})
    if args.limit:
        plan = plan[: args.limit]
    return plan, meta


def print_plan(plan):
    by_dialog: dict[tuple, list] = {}
    for p in plan:
        by_dialog.setdefault(tuple(p["path"]), []).append(p)
    todo = sum(1 for p in plan if not p["skip_existing"])
    print(f"\n{todo} variant(s) to add across {len(by_dialog)} dialog(s) "
          f"({len(plan) - todo} already present, skipped):\n")
    for path, items in by_dialog.items():
        print(f"  {' / '.join(path)}")
        for p in items:
            tag = "SKIP (exists)" if p["skip_existing"] else f"ADD  [{p['group']}]"
            print(f"    {tag}")
            print(f"      en-GB: {p['en']}")
            print(f"      ro-RO: {p['ro']}")
        print()


# --------------------------------------------------------------------------
# browser side (only imported/used with --apply)
# --------------------------------------------------------------------------
async def run_apply(plan, args, meta):
    sys.path.insert(0, str(HERE.parent / "coaching-bundle-export"))
    from playwright.async_api import async_playwright
    import _menu_nav as S

    async def pick_page(ctx):
        for pg in ctx.pages:
            try:
                if await pg.evaluate("() => !!document.querySelector('.v-menubar.md-menu')"):
                    return pg
            except Exception:  # noqa: BLE001
                pass
        return ctx.pages[0] if ctx.pages else None

    def rg_col(headers):
        return next((i for i, h in enumerate(headers)
                     if "andomis" in h or "andomiz" in h), None)

    # the .v-table body is virtualized - only on-screen rows are in the DOM.
    # scroll top-to-bottom, and place each rendered row by its pixel position
    # within the scroll content (row_top - scroller_top + scrollTop) / rowHeight
    # -- same technique as _menu_nav.sweep_table.
    TABLE_JS = r"""
    async () => {
      const t = document.querySelector('.v-table');
      if (!t) return { headers: [], rows: [] };
      const headers = [...t.querySelectorAll('.v-table-header-cell .v-table-caption-container')]
        .map(e => e.textContent.trim());
      const sc = t.querySelector('.v-table-body-wrapper')
        || t.querySelector('.v-scrollable')
        || t.querySelector('.v-table-body').parentElement;
      const first = t.querySelector('.v-table-body tr');
      const rh = first ? first.offsetHeight || 24 : 24;
      const map = new Map();
      const grab = () => {
        const base = sc.getBoundingClientRect().top;
        t.querySelectorAll('.v-table-body tr').forEach(tr => {
          const cells = [...tr.querySelectorAll('.v-table-cell-wrapper')].map(c => c.textContent.trim());
          if (!cells.length) return;
          const idx = Math.round((tr.getBoundingClientRect().top - base + sc.scrollTop) / rh);
          if (idx >= 0) map.set(idx, cells);
        });
      };
      const total = Math.max(Math.round(sc.scrollHeight / rh),
                             t.querySelectorAll('.v-table-body tr').length);
      sc.scrollTop = 0; await new Promise(r => setTimeout(r, 150)); grab();
      const step = Math.max(rh * 3, 120);
      let guard = 0;
      while (sc.scrollTop + sc.clientHeight < sc.scrollHeight - 2 && guard++ < 2000) {
        sc.scrollTop += step; await new Promise(r => setTimeout(r, 130)); grab();
      }
      sc.scrollTop = sc.scrollHeight; await new Promise(r => setTimeout(r, 200)); grab();
      // fill any index still missing with a targeted scroll
      for (let i = 0; i < total; i++) {
        if (map.has(i)) continue;
        sc.scrollTop = Math.max(0, i * rh - sc.clientHeight / 2);
        await new Promise(r => setTimeout(r, 160)); grab();
      }
      const rows = [];
      for (let i = 0; i < total; i++) rows.push(map.get(i) || []);
      return { headers, rows };
    }
    """

    async def read_table(page):
        d = await page.evaluate(TABLE_JS)
        return d["headers"], d["rows"]

    def grp_rows(rows, gi, group):
        return [k for k, r in enumerate(rows)
                if gi is not None and gi < len(r) and r[gi].strip() == group]

    async def wait_table(page, pred, tries=60, gap=300):
        """Poll read_table until pred(heads, rows) is truthy."""
        heads, rows = await read_table(page)
        for _ in range(tries):
            if pred(heads, rows):
                break
            await page.wait_for_timeout(gap)
            heads, rows = await read_table(page)
        return heads, rows

    # .v-table is virtualized - work in LOGICAL row indices (pixel position /
    # row height), never DOM child order.
    async def selected_row(page):
        return await page.evaluate(r"""
        () => {
          const t = document.querySelector('.v-table'); if (!t) return -1;
          const sc = t.querySelector('.v-table-body-wrapper') || t.querySelector('.v-scrollable');
          const f = t.querySelector('.v-table-body tr'); const rh = f ? (f.offsetHeight||24) : 24;
          const base = sc.getBoundingClientRect().top;
          for (const tr of t.querySelectorAll('.v-table-body tr'))
            if ((tr.className||'').includes('v-selected'))
              return Math.round((tr.getBoundingClientRect().top - base + sc.scrollTop) / rh);
          return -1;
        }""")

    async def click_row(page, idx):
        """Scroll logical row `idx` into view and click it. Returns True on hit.
        Polls after scrolling - the virtual body needs time to re-render when
        the table was scrolled far from the target."""
        hit = await page.evaluate(r"""
        async (idx) => {
          const t = document.querySelector('.v-table'); if (!t) return null;
          const sc = t.querySelector('.v-table-body-wrapper') || t.querySelector('.v-scrollable');
          const rows = [...t.querySelectorAll('.v-table-body tr')].filter(
            tr => tr.querySelector('.v-table-cell-wrapper'));
          const rh = rows.length ? (rows[0].offsetHeight || 24) : 24;
          const want = idx * rh;
          const at = () => {
            const base = sc.getBoundingClientRect().top;
            for (const tr of t.querySelectorAll('.v-table-body tr')) {
              if (!tr.querySelector('.v-table-cell-wrapper')) continue;
              const p = Math.round((tr.getBoundingClientRect().top - base + sc.scrollTop) / rh);
              if (p === idx) return tr;
            }
            return null;
          };
          let tr = at();
          if (!tr) {
            sc.scrollTop = Math.max(0, want - sc.clientHeight / 2);
            for (let i = 0; i < 20 && !tr; i++) {
              await new Promise(r => setTimeout(r, 150));
              tr = at();
            }
          }
          if (!tr) return null;
          const r = tr.getBoundingClientRect();
          return { x: r.x + Math.min(r.width / 2, 300), y: r.y + r.height / 2 };
        }""", idx)
        if not hit:
            return False
        await page.mouse.click(hit["x"], hit["y"])
        await page.wait_for_timeout(450)
        return True

    async def select_row(page, idx):
        """Select logical row `idx`. Clicking an already-selected Vaadin row
        toggles selection OFF, so skip if it is already current."""
        if await selected_row(page) == idx:
            return
        if not await click_row(page, idx):
            raise RuntimeError(f"row {idx} not found to select")
        await page.wait_for_timeout(300)

    async def dbg(page, tag):
        if not args.debug:
            return
        d = await page.evaluate(r"""
        () => {
          const t = document.querySelector('.v-table');
          const bodyRows = t ? [...t.querySelectorAll('.v-table-body tr')] : [];
          const sel = bodyRows.findIndex(r => (r.className||'').includes('v-selected'));
          const eds = [...document.querySelectorAll('.v-button')].filter(b =>
            ((b.querySelector('.v-button-caption')||{}).textContent||'').trim() === 'Edit')
            .map(b => { const r = b.getBoundingClientRect();
              return { x: Math.round(r.x), y: Math.round(r.y),
                       dis: (b.className||'').includes('v-disabled') }; });
          return { wins: document.querySelectorAll('.v-window').length,
                   rows: bodyRows.length, selected: sel, edits: eds };
        }
        """)
        print(f"    [dbg {tag}] wins={d['wins']} rows={d['rows']} "
              f"selectedRow={d['selected']} Edit={d['edits']}")

    async def node_btn(page, caption, timeout=6000):
        """A node-toolbar button (in the .micro-dialogs layout, left of the
        row-action column, not '<caption> Dialog'). Polls until it is enabled -
        the toolbar re-renders disabled->enabled on a server round-trip after a
        row is selected."""
        loc = page.locator(".v-button", has=page.locator(
            f".v-button-caption:text-is('{caption}')"))
        deadline = asyncio.get_event_loop().time() + timeout / 1000
        while True:
            for i in range(await loc.count()):
                b = loc.nth(i)
                box = await b.bounding_box()
                if not box or box["x"] > 1600:      # row-action column, far right
                    continue
                cls = await b.get_attribute("class") or ""
                if "v-disabled" not in cls:
                    return b
            if asyncio.get_event_loop().time() > deadline:
                return None
            await page.wait_for_timeout(300)

    async def dismiss(page, keep=0):
        for _ in range(10):
            wins = page.locator(".v-window")
            n = await wins.count()
            if n <= keep:
                return
            top = wins.nth(n - 1)
            done = False
            for lbl in ("Cancel", "Close"):
                btn = top.locator(".v-button-caption", has_text=lbl)
                if await btn.count():
                    try:
                        await btn.first.click(timeout=2500)
                        done = True
                    except Exception:  # noqa: BLE001
                        pass
                    break
            if not done:
                await page.keyboard.press("Escape")
            await page.wait_for_timeout(500)

    async def set_lang_text(page, lang_caption, text):
        sub = page.locator(".v-window").last
        await sub.locator(".v-button-caption", has_text=lang_caption).first.click()
        await page.wait_for_timeout(400)
        ta = sub.locator("textarea").first
        await ta.click()
        await ta.fill(text)
        await page.wait_for_timeout(200)

    added = errors = skipped = 0
    async with async_playwright() as pw:
        b = await pw.chromium.connect_over_cdp(CDP)
        ctx = b.contexts[0]
        page = await pick_page(ctx)
        if not page:
            sys.exit("no logged-in PMCP tab found on the CDP browser")
        # accept native confirm() dialogs (Playwright dismisses them by default)
        page.on("dialog", lambda d: asyncio.ensure_future(d.accept()))
        cdp = await ctx.new_cdp_session(page)
        wid = (await cdp.send("Browser.getWindowForTarget"))["windowId"]
        await cdp.send("Browser.setWindowBounds", {"windowId": wid, "bounds": {
            "left": 0, "top": 0, "width": 3600, "height": 1800, "windowState": "normal"}})
        await page.wait_for_timeout(1000)

        NEG = {"cancel", "no", "abbrechen", "nein", "close", "anulează", "nu"}

        async def confirm(page):
            """Wait for the 'are you sure?' popup and click its affirmative
            button (anything not obviously a cancel, so locale variants work)."""
            try:
                await page.wait_for_selector(".v-window", timeout=5000)
            except Exception:  # noqa: BLE001
                return  # no popup (or a native dialog already auto-accepted)
            for _ in range(5):
                w = page.locator(".v-window")
                if not await w.count():
                    return
                caps = [c.strip() for c in await w.last.locator(
                    ".v-button-caption").all_inner_texts()]
                print(f"    [confirm] popup buttons: {caps}")
                pos = next((c for c in caps if c and c.lower() not in NEG), None)
                if not pos:
                    print("    [confirm] no affirmative button found!")
                    return
                await w.last.locator(".v-button-caption", has_text=pos).first.click()
                await page.wait_for_timeout(700)

        try:
            await dismiss(page)

            if args.dedup:
                pool = args.pool or (plan[0]["pool"] if plan else None)
                m = meta.get(pool) if pool else None
                if not m:
                    sys.exit("--dedup needs --pool 'r_X @ Micro Dialog' that exists in the CSV")
                path, group = menu_path(m), m["group"]
                await S.navigate_and_select(page, path)
                await S.wait_round_trip(page)
                removed = 0
                for _ in range(40):
                    heads, rows = await read_table(page)
                    gi = rg_col(heads)
                    ti = next((i for i, h in enumerate(heads) if "Message Text" in h), 2)
                    seen, dup_idx = set(), None
                    for k, r in enumerate(rows):
                        if gi is None or gi >= len(r) or r[gi].strip() != group:
                            continue
                        txt = r[ti] if ti < len(r) else ""
                        if txt in seen:
                            dup_idx = k          # a later exact copy of an earlier sibling
                        else:
                            seen.add(txt)
                    if dup_idx is None:
                        break
                    n_before = sum(1 for r in rows if r)
                    print(f"  - deleting dup row {dup_idx}: {rows[dup_idx][ti][:70]!r}")
                    await select_row(page, dup_idx)
                    if await selected_row(page) != dup_idx:
                        print(f"  ! could not select row {dup_idx} (got "
                              f"{await selected_row(page)}); stopping"); break
                    d = await node_btn(page, "Delete")
                    if not d:
                        print("  ! no enabled Delete button"); break
                    await d.click()
                    await page.wait_for_timeout(700)
                    await confirm(page)
                    # do not read/scroll the table until the popup is gone
                    for _ in range(20):
                        if not await page.locator(".v-window").count():
                            break
                        await page.wait_for_timeout(300)
                    await S.wait_round_trip(page)
                    heads, rows = await wait_table(
                        page, lambda h, rs: sum(1 for r in rs if r) < n_before, tries=25)
                    if sum(1 for r in rows if r) >= n_before:
                        print("  ! delete did not take (row count unchanged); stopping")
                        break
                    removed += 1
                print(f"\n{pool}: removed {removed} duplicate row(s)")
                return

            for p in plan:
                if p["skip_existing"]:
                    skipped += 1
                    continue
                label = f"{' / '.join(p['path'])}  [{p['group']}]  {p['en'][:40]!r}"
                try:
                    await S.navigate_and_select(page, p["path"])
                    await S.wait_round_trip(page)
                    heads, rows = await read_table(page)
                    gi = rg_col(heads)
                    src = next((k for k, r in enumerate(rows)
                                if gi is not None and gi < len(r)
                                and r[gi].strip() == p["group"]), None)
                    if src is None:
                        print(f"  ! {label}: no existing row with this group"); errors += 1
                        continue
                    ci = next((i for i, h in enumerate(heads) if "Message Text" in h), None)
                    ci = ci if ci is not None else 2
                    ti = ci
                    grp = grp_rows(rows, gi, p["group"])
                    # the grid truncates long text, so match a short prefix of
                    # en-GB within this group's rows.
                    key = p["en"].strip()[:18]
                    have = [k for k in grp if key and key in (rows[k][ci] if ci < len(rows[k]) else "")]
                    reposition_only = False
                    if have:
                        k = have[0]
                        if k > 0 and gi < len(rows[k - 1]) and rows[k - 1][gi].strip() == p["group"]:
                            print(f"  = {label}: already in the pool (row {k}), skipped")
                            skipped += 1
                            continue
                        print(f"  ~ {label}: present at row {k} but not adjacent - "
                              "repositioning only")
                        new_idx = k
                        reposition_only = True

                    tr = page.locator(".v-table .v-table-body tr")
                    # failed-run recovery: an unedited exact copy already sitting
                    # in the group after the original(s) -> reuse it, don't
                    # stack another Duplicate.
                    src_texts = {rows[j][ci] for j in grp if j <= src}
                    strays = [k for k in grp if k > src and ci < len(rows[k])
                              and rows[k][ci] in src_texts]
                    if reposition_only:
                        pass                              # new_idx already set; skip add
                    elif strays:
                        new_idx = strays[-1]
                        print(f"  ~ {label}: reusing stray copy at row {new_idx}")
                        await select_row(page, new_idx)
                    else:
                        await select_row(page, src)
                        await dbg(page, "src selected")
                        dup = await node_btn(page, "Duplicate")
                        if not dup:
                            print(f"  ! {label}: no Duplicate button"); errors += 1
                            continue
                        n_before = len(grp)
                        await dup.click()
                        heads, rows = await wait_table(
                            page, lambda h, rs: len(grp_rows(rs, rg_col(h), p["group"])) > n_before)
                        await dismiss(page)  # any confirm popup
                        heads, rows = await read_table(page)
                        grp = grp_rows(rows, gi, p["group"])
                        if len(grp) <= n_before:
                            print(f"  ! {label}: Duplicate did not add a row"); errors += 1
                            continue
                        new_idx = grp[-1]           # the copy = last row of the group
                    await dbg(page, "after Duplicate/reuse")

                    if not reposition_only:
                        await select_row(page, new_idx)
                        await dbg(page, f"new row {new_idx}")
                        ed = await node_btn(page, "Edit")
                        if not ed:
                            print(f"  ! {label}: no node Edit button"); errors += 1
                            continue
                        await ed.click()
                        try:  # wait for the message modal's text row to render
                            await page.wait_for_function(
                                r"""() => { const w = document.querySelector('.v-window');
                                return w && [...w.querySelectorAll('.v-label')].some(
                                  e => /text \(with placeholders\)/i.test(e.textContent)); }""",
                                timeout=12000)
                        except Exception:  # noqa: BLE001
                            pass
                        await page.wait_for_timeout(400)
                        await dbg(page, "after Edit click")

                        # the Edit next to "text (with placeholders):"
                        spot = await page.evaluate(r"""
                        () => {
                          const w = document.querySelector('.v-window'); if (!w) return null;
                          const l = [...w.querySelectorAll('.v-label')]
                            .find(e => /text \(with placeholders\)/i.test(e.textContent));
                          if (!l) return null;
                          const ly = l.getBoundingClientRect().top;
                          let best = null, bd = 1e9;
                          w.querySelectorAll('.v-button').forEach(x => {
                            if (((x.querySelector('.v-button-caption')||{}).textContent||'').trim() !== 'Edit') return;
                            const r = x.getBoundingClientRect(), d = Math.abs(r.top - ly);
                            if (d < bd) { bd = d; best = {x: Math.round(r.x+r.width/2), y: Math.round(r.top+r.height/2)}; }
                          });
                          return best;
                        }
                        """)
                        if not spot:
                            print(f"  ! {label}: text-row Edit not found"); errors += 1
                            await dismiss(page)
                            continue
                        await page.mouse.click(spot["x"], spot["y"])
                        try:  # wait for the text sub-editor (has the OK button)
                            await page.wait_for_selector(
                                ".v-window .v-button-caption:has-text('OK')", timeout=8000)
                        except Exception:  # noqa: BLE001
                            pass
                        await page.wait_for_timeout(400)

                        await set_lang_text(page, "English (GB)", p["en"])
                        await set_lang_text(page, "Romanian (RO)", p["ro"])
                        await page.locator(".v-window").last.locator(
                            ".v-button-caption", has_text="OK").first.click()
                        await page.wait_for_timeout(800)
                        await dismiss(page)  # close the outer message modal

                    # Move Up: the grid truncates long text, so don't track the
                    # row by full-text match. Instead: the new row is grp[-1];
                    # move it to just after grp[-2] with a fixed number of clicks
                    # (it stays selected and shifts up one per click), then
                    # verify once at the end with a short (untruncated) prefix.
                    en = p["en"].strip()
                    key = en[:18]
                    heads, rows = await read_table(page)
                    grp = grp_rows(rows, gi, p["group"])
                    n_up = 0
                    if len(grp) >= 2:
                        start, target = grp[-1], grp[-2] + 1
                        n_up = min(max(0, start - target), 300)
                        for i in range(n_up):
                            want = start - i
                            if await selected_row(page) != want:
                                await select_row(page, want)
                            mu = await node_btn(page, "Move Up")
                            if not mu:
                                break
                            await mu.click()
                            await S.wait_round_trip(page)
                            await page.wait_for_timeout(120)
                    heads, rows = await read_table(page)
                    cur = next((k for k, r in enumerate(rows)
                                if ti < len(r) and key and key in r[ti]
                                and gi is not None and gi < len(r)
                                and r[gi].strip() == p["group"]), None)
                    adj = (cur is not None and cur > 0 and gi is not None
                           and gi < len(rows[cur - 1])
                           and rows[cur - 1][gi].strip() == p["group"])
                    await dbg(page, "after Move Up loop")
                    if not adj:
                        errors += 1
                    print(f"  {'+' if adj else '!'} {label}  (row {cur}, {n_up} moves, "
                          f"{'adjacent to pool' if adj else 'NOT adjacent - check'})")
                    if adj:
                        added += 1
                except Exception as e:  # noqa: BLE001
                    print(f"  !! {label}: {e!r}")
                    errors += 1
                    await dismiss(page)
        finally:
            await cdp.send("Browser.setWindowBounds", {"windowId": wid, "bounds": {
                "left": 60, "top": 60, "width": 1500, "height": 1000, "windowState": "normal"}})
    print(f"\nadded={added}  skipped={skipped}  errors={errors}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true",
                    help="actually write (default: dry run, navigate + report only)")
    ap.add_argument("--limit", type=int, required=True,
                    help="REQUIRED: cap the number of variants added")
    ap.add_argument("--pool", help="only this pool (e.g. 'r_X @ Micro Dialog')")
    ap.add_argument("--dedup", action="store_true",
                    help="delete rows in --pool whose text exactly copies an "
                         "earlier sibling in the same group (clean up failed runs)")
    ap.add_argument("--debug", action="store_true", help="verbose per-step state dump")
    args = ap.parse_args()

    plan, meta = build_plan(args)

    if args.dedup:
        if not args.pool:
            sys.exit("--dedup requires --pool 'r_X @ Micro Dialog'")
        if not args.apply:
            print(f"dry run - would de-dup pool {args.pool!r} in the live editor. "
                  "Pass --apply to do it.")
            return
        asyncio.run(run_apply(plan, args, meta))
        return

    print_plan(plan)
    if not args.apply:
        print("dry run - pass --apply to write. Nothing was changed.")
        return
    todo = [p for p in plan if not p["skip_existing"]]
    if not todo:
        print("nothing to add.")
        return
    asyncio.run(run_apply(plan, args, meta))


if __name__ == "__main__":
    main()
