"""Discovery spike for Stage 3 (write-back): map the message-edit modal.

The add-a-variant recipe (confirmed by hand in PMCP) is:

  1. select an existing message that is already in the target r_ group
  2. click **Duplicate** (the node button, NOT "Duplicate Dialog") -> a copy is
     appended at the BOTTOM of the message list, keeping the r_ group
  3. select that new bottom row, click **Edit** -> change en-GB + ro-RO text
  4. click **Move Up** until it sits next to the rest of the group
     (a randomisation group only fires when its messages are consecutive)

Duplicate / Move Up / Move Down / Delete are plain list ops with no modal - the
button dump already confirms their captions. The ONLY modal in the flow is the
message editor, and its open questions are:

  * how are en-GB and ro-RO entered? (language dropdown that swaps one field?
    two fields? a tab?)
  * what commits the change - a Save/OK button, or does "Close" commit?
  * where does the randomisation-group value show (to confirm Duplicate keeps it)

So this spike selects an existing r_-group message, opens **Edit**, deep-dumps
the modal (every input / textarea / rich-text / combo with its label + value +
position, every button, the full HTML), then dismisses via "Close". It does NOT
type and does NOT click Save. Sandbox coaching only ("ALEX v01 zum
Ausprobieren"), all writes there are logged anyway.

  ./probe_add_message.sh "👋 Hello" "Morning greetings"

Output: tools/coaching-bundle-export/spike/edit_*.
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from playwright.async_api import async_playwright

import _menu_nav as S

HERE = Path(__file__).resolve().parent
OUT = HERE / "spike"
OUT.mkdir(exist_ok=True)
CDP = os.environ.get("PMCP_CDP", "http://127.0.0.1:9222")

DEFAULT_TARGETS = [
    ["👋 Hello", "Morning greetings"],
    ["Timeless Greetings"],
    ["Daytime Greetings"],
    ["Morning greetings"],
]

# --- table read: rows + which column is Randomisation Group -----------------
TABLE_JS = r"""
() => {
  const t = document.querySelector('.v-table');
  if (!t) return { headers: [], rows: [] };
  const headers = [...t.querySelectorAll('.v-table-header-cell .v-table-caption-container')]
    .map(e => e.textContent.trim());
  const rows = [...t.querySelectorAll('.v-table-body tr')].map((tr, i) => ({
    i,
    cells: [...tr.querySelectorAll('.v-table-cell-wrapper')].map(c => c.textContent.trim()),
  }));
  return { headers, rows };
}
"""

# every visible button (page-wide), sorted top-to-bottom
BUTTONS_JS = r"""
() => {
  const cls = (el) => {
    const c = el.getAttribute && el.getAttribute('class');
    return (typeof c === 'string' ? c : '') || '';
  };
  const anc = (el) => {
    const out = [];
    for (let p = el.parentElement, i = 0; p && i < 14; i++, p = p.parentElement)
      if (cls(p)) out.push(cls(p));
    return out.join(' | ');
  };
  return [...document.querySelectorAll('.v-button')].map(bt => {
    const r = bt.getBoundingClientRect();
    const icon = bt.querySelector('.v-icon, img');
    return {
      caption: ((bt.querySelector('.v-button-caption') || {}).textContent || '')
        .replace(/\s+/g, ' ').trim(),
      iconFile: icon && icon.tagName === 'IMG'
        ? (icon.getAttribute('src') || '').split('/').pop() : (icon ? cls(icon) : ''),
      disabled: bt.hasAttribute('disabled') || cls(bt).includes('v-disabled'),
      inModal: !!bt.closest('.v-window'),
      x: Math.round(r.x), y: Math.round(r.y),
      w: Math.round(r.width), h: Math.round(r.height),
      visible: r.width > 0 && r.height > 0,
      ancestry: anc(bt),
    };
  }).sort((a, b) => a.y - b.y || a.x - b.x);
}
"""

# deep dump of every open .v-window
MODAL_JS = r"""
() => [...document.querySelectorAll('.v-window')].map(w => {
  const near = (el) => {
    // nearest caption text: previous .v-caption sibling, or ancestor's
    for (let p = el; p && p !== w; p = p.parentElement) {
      let s = p.previousElementSibling;
      while (s) {
        if (s.classList && s.classList.contains('v-caption')) return s.textContent.replace(/\s+/g,' ').trim();
        s = s.previousElementSibling;
      }
      const c = p.querySelector && p.querySelector(':scope > .v-caption');
      if (c) return c.textContent.replace(/\s+/g,' ').trim();
    }
    return '';
  };
  const rect = (el) => { const r = el.getBoundingClientRect();
    return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; };
  const controls = [];
  w.querySelectorAll('input, textarea, [contenteditable="true"], .v-richtextarea, .v-filterselect, .v-select, .v-checkbox, .v-select-optiongroup').forEach(el => {
    const tag = el.tagName.toLowerCase();
    const kind = el.className && typeof el.className === 'string'
      ? (el.className.split(' ').find(c => /^v-(textfield|textarea|richtextarea|filterselect|select|checkbox|optiongroup)/.test(c)) || tag)
      : tag;
    let val = '';
    if (tag === 'input' || tag === 'textarea') val = el.value || '';
    else if (el.getAttribute && el.getAttribute('contenteditable')) val = el.textContent || '';
    else {
      const inp = el.querySelector && el.querySelector('input,textarea');
      val = inp ? (inp.value || '') : (el.textContent || '');
    }
    controls.push({
      kind, tag, label: near(el),
      value: (val || '').replace(/\s+/g,' ').trim().slice(0, 160),
      id: el.id || '', cls: (typeof el.className === 'string' ? el.className : ''),
      ...rect(el),
    });
  });
  const buttons = [...w.querySelectorAll('.v-button')].map(b => ({
    caption: ((b.querySelector('.v-button-caption') || {}).textContent || '').replace(/\s+/g,' ').trim(),
    disabled: b.hasAttribute('disabled') || (typeof b.className==='string' && b.className.includes('v-disabled')),
    ...rect(b),
  }));
  const tabs = [...w.querySelectorAll('.v-tabsheet-tabitemcell, .v-tabsheet-tabitem')]
    .map(e => e.textContent.replace(/\s+/g,' ').trim()).filter(Boolean);
  const langBits = [...new Set([...w.querySelectorAll('*')].map(e => (e.textContent||'').trim())
    .filter(t => t && t.length < 30 && /en-?GB|ro-?RO|English|Roman|Deutsch|German|Language|Sprache|Limba/i.test(t)))];
  return {
    caption: ((w.querySelector('.v-window-header') || {}).textContent || '').replace(/\s+/g,' ').trim(),
    tabs, langBits, controls, buttons,
    html: w.outerHTML.slice(0, 200000),
  };
});
"""


async def pick_page(ctx):
    for p in ctx.pages:
        try:
            if await p.evaluate("() => !!document.querySelector('.v-menubar.md-menu')"):
                return p
        except Exception:  # noqa: BLE001
            pass
    return ctx.pages[0] if ctx.pages else None


async def try_select(page, targets):
    for labels in targets:
        try:
            await S.navigate_and_select(page, labels)
            await S.wait_round_trip(page)
            if await page.locator(".v-table .v-table-body tr").count():
                print(f"selected {labels}")
                return labels
        except Exception as e:  # noqa: BLE001
            print(f"  {labels} -> {e!r}")
    return None


async def dismiss(page):
    """Close windows top-down. A stacked modal's curtain blocks clicks on the
    ones beneath it, so always act on the LAST .v-window (topmost) and fall
    back to Escape when a click is intercepted."""
    for _ in range(10):
        wins = page.locator(".v-window")
        n = await wins.count()
        if not n:
            return
        top = wins.nth(n - 1)
        clicked = False
        for label in ("Cancel", "Close", "Abbrechen", "Anulează", "Exit"):
            btn = top.locator(".v-button-caption", has_text=label)
            if await btn.count():
                try:
                    await btn.first.click(timeout=2500)
                    print(f"  dismiss via {label!r} ({n} open)")
                    clicked = True
                except Exception:  # noqa: BLE001
                    pass
                break
        if not clicked:
            await page.keyboard.press("Escape")
        await page.wait_for_timeout(600)


async def main():
    env = os.environ.get("PROBE_LABELS")
    targets = [json.loads(env)] if env else DEFAULT_TARGETS

    async with async_playwright() as pw:
        b = await pw.chromium.connect_over_cdp(CDP)
        ctx = b.contexts[0]
        page = await pick_page(ctx)
        if page is None:
            print("no pages on the CDP browser"); return
        print(f"attached tab: {page.url}")
        cdp = await ctx.new_cdp_session(page)
        wid = (await cdp.send("Browser.getWindowForTarget"))["windowId"]
        await cdp.send("Browser.setWindowBounds", {"windowId": wid, "bounds": {
            "left": 0, "top": 0, "width": 3600, "height": 2000, "windowState": "normal"}})
        await page.wait_for_timeout(1200)
        try:
            # clear any modal left open by a previous aborted run
            if await page.locator(".v-window").count():
                print("clearing stale modal(s)...")
                await dismiss(page)

            if not await try_select(page, targets):
                d = await page.evaluate(
                    "() => ({url: location.href, menu: !!document.querySelector('.v-menubar.md-menu'),"
                    " login: !!document.querySelector('input[type=password]')})")
                print(f"\ncould not select a dialog: {d}")
                print("open <coaching> -> Edit -> Micro Dialogs (Monitoring inactive), "
                      "click a dialog, then rerun.")
                return

            tbl = await page.evaluate(TABLE_JS)
            heads = tbl["headers"]
            print(f"\ncolumns: {heads}")
            rg_col = next((i for i, h in enumerate(heads)
                           if "andomis" in h or "andomiz" in h), None)
            target_row = None
            for r in tbl["rows"]:
                cells = r["cells"]
                v = cells[rg_col] if rg_col is not None and rg_col < len(cells) else ""
                if v.startswith("r_"):
                    target_row = r
                    print(f"row {r['i']}: r_group={v!r}  text={' | '.join(cells)[:90]!r}")
                    break
            if target_row is None:
                print("no row with an r_ randomisation group in this dialog; "
                      "pass one that has a pool (e.g. a greetings dialog).")
                return

            rows = page.locator(".v-table .v-table-body tr")
            await rows.nth(target_row["i"]).click()
            await page.wait_for_timeout(700)

            buttons = await page.evaluate(BUTTONS_JS)
            (OUT / "edit_buttons.json").write_text(
                json.dumps(buttons, indent=1, ensure_ascii=False))
            vis = [b for b in buttons if b["visible"] and not b["inModal"]]
            # the node toolbar row: the y of "New Message" (with add-icon)
            nm = next((b for b in vis if b["caption"] == "New Message"), None)
            toolbar_y = nm["y"] if nm else None
            edit = None
            if toolbar_y is not None:
                edit = next((b for b in vis if b["caption"] == "Edit"
                             and abs(b["y"] - toolbar_y) < 6 and not b["disabled"]), None)
            if not edit:  # fallback: leftmost enabled "Edit" not in the row action column
                cand = [b for b in vis if b["caption"] == "Edit" and not b["disabled"]
                        and b["x"] < 2000]
                edit = min(cand, key=lambda b: b["x"]) if cand else None
            print("\nnode toolbar buttons:",
                  [b["caption"] for b in vis if toolbar_y and abs(b["y"] - toolbar_y) < 6])
            if not edit:
                print("could not locate the node-toolbar Edit button; see edit_buttons.json")
                return
            print(f"clicking node Edit @({edit['x']},{edit['y']})")
            await page.mouse.click(edit["x"] + edit["w"] / 2, edit["y"] + edit["h"] / 2)
            await page.wait_for_timeout(1600)

            modal = await page.evaluate(MODAL_JS)
            (OUT / "edit_modal.json").write_text(
                json.dumps(modal, indent=1, ensure_ascii=False))
            try:
                await page.screenshot(path=str(OUT / "edit_modal.png"),
                                      timeout=8000, full_page=True)
            except Exception as e:  # noqa: BLE001
                print(f"  (screenshot skipped: {e!r})")

            def show(tag, mods):
                if not mods:
                    print(f"\n{tag}: no modal")
                for w in mods:
                    print(f"\n{tag} {w['caption']!r}")
                    print(f"  tabs    : {w['tabs']}")
                    print(f"  langBits: {w['langBits']}")
                    print(f"  buttons : {[b['caption'] for b in w['buttons'] if b['caption']]}")
                    print("  controls:")
                    for c in w["controls"]:
                        print(f"    [{c['kind']:16}] label={c['label'][:28]!r:30} "
                              f"val={c['value'][:46]!r} @({c['x']},{c['y']} {c['w']}x{c['h']})")

            show("outer modal", modal)

            # find the Edit button that belongs to the "text (with placeholders)"
            # row and open that nested editor - that's where en-GB / ro-RO text
            # is actually entered
            spot = await page.evaluate(r"""
            () => {
              const w = document.querySelector('.v-window'); if (!w) return null;
              const lbl = [...w.querySelectorAll('.v-label')]
                .find(e => /text \(with placeholders\)/i.test(e.textContent));
              if (!lbl) return null;
              const ly = lbl.getBoundingClientRect().top;
              let best = null, bd = 1e9;
              w.querySelectorAll('.v-button').forEach(b => {
                const cap = ((b.querySelector('.v-button-caption')||{}).textContent||'').trim();
                if (cap !== 'Edit') return;
                const r = b.getBoundingClientRect();
                const d = Math.abs(r.top - ly);
                if (d < bd) { bd = d; best = { x: Math.round(r.x+r.width/2), y: Math.round(r.top+r.height/2), d: Math.round(d) }; }
              });
              return best;
            }
            """)
            if not spot:
                print("\ncould not find the text-row Edit button; see edit_modal.json")
            else:
                print(f"\nopening text sub-editor: Edit @({spot['x']},{spot['y']}) dy={spot['d']}")
                await page.mouse.click(spot["x"], spot["y"])
                await page.wait_for_timeout(1500)
                sub = await page.evaluate(MODAL_JS)
                (OUT / "edit_textmodal.json").write_text(
                    json.dumps(sub, indent=1, ensure_ascii=False))
                try:
                    await page.screenshot(path=str(OUT / "edit_textmodal.png"),
                                          timeout=8000, full_page=True)
                except Exception as e:  # noqa: BLE001
                    print(f"  (screenshot skipped: {e!r})")
                # the newest / topmost window is the sub-editor
                show("text sub-editor (all windows)", sub)

            await dismiss(page)
            still = await page.evaluate("() => document.querySelectorAll('.v-window').length")
            print(f"\nwindows open after dismiss: {still} (expect 0)")
            print(f"\nartifacts: {OUT}/  edit_buttons.json, edit_modal.json/png, "
                  "edit_textmodal.json/png")
        finally:
            await cdp.send("Browser.setWindowBounds", {"windowId": wid, "bounds": {
                "left": 60, "top": 60, "width": 1500, "height": 1000, "windowState": "normal"}})
            print("window restored")


if __name__ == "__main__":
    asyncio.run(main())
