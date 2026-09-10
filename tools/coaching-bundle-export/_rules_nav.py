"""Shared toolkit for the PMCP **Rules tab** (a Vaadin 7 `.v-tree`).

Used by `probe_rules_tree.py` (discovery) and `export_rules.py` (production).
The menubar equivalent is `_menu_nav.py`.

Vaadin 7 tree facts confirmed live 2026-09-10 (see
`autochanges/2026-09-10-rules-tree-stage3-sweep.md`):
  - expand state is the `aria-expanded="true|false"` attribute, not a class;
    absent = leaf OR never-opened parent (indistinguishable until tried).
  - children are pre-rendered but hidden; `.v-tree-node` COUNT never changes
    on expand -> use caption visibility (`rect.width>0`) as the signal.
  - expand gesture: click the caption AT x=20 (a short caption's box centre
    is dead space Vaadin ignores), wait ~600ms for the selection round-trip,
    THEN ArrowRight.
  - opening a node lazy-loads its children and shifts every later sibling
    index -> re-dump after every expansion, match by (depth, caption).
  - the "Edit rule:" modal is `v-window v-readonly`; filterselect values are
    only in the live `.value` DOM property, never the HTML attribute.
"""
from __future__ import annotations

import re

TREE_DUMP_JS = r"""
() => {
  const trees = [...document.querySelectorAll('.v-tree')];
  const dump = (tree) => {
    const nodes = [...tree.querySelectorAll('.v-tree-node[role=treeitem]')];
    return nodes.map((n, i) => {
      const capEl = n.querySelector(':scope > .v-tree-node-caption');
      const cap = capEl ? capEl.textContent.replace(/\s+/g, ' ').trim() : '';
      const iconEl = capEl ? capEl.querySelector('img.v-icon, .v-icon') : null;
      const icon = (iconEl ? (iconEl.getAttribute('src') || iconEl.className) : '').split('/').pop();
      const kids = n.querySelector(':scope > .v-tree-node-children');
      const r = capEl ? capEl.getBoundingClientRect() : {width: 0, height: 0, top: 0};
      const aria = n.getAttribute('aria-expanded');
      return {
        i,
        depth: parseInt(n.getAttribute('aria-level') || '1', 10) - 1,
        caption: cap, classes: n.className, icon,
        ariaExpanded: aria,
        hasChildEls: !!kids && kids.childElementCount > 0,
        visible: r.width > 0 && r.height > 0,
        expanded: aria === 'true',
        leaf: aria === null && !(kids && kids.childElementCount > 0),
        rectTop: Math.round(r.top),
      };
    });
  };
  return trees.map((t, ti) => ({
    treeIndex: ti, classes: t.className,
    nodeCount: t.querySelectorAll('.v-tree-node[role=treeitem]').length,
    nodes: dump(t),
    outerHTMLHead: t.outerHTML.slice(0, 3000),
  }));
}
"""

RULE_MODAL_JS = r"""
() => {
  const w = [...document.querySelectorAll('.v-window')].pop();
  if (!w) return { error: 'no .v-window' };
  const norm = s => (s || '').replace(/\s+/g, ' ').trim();

  const ITEM_SEL = '.v-label, .v-checkbox, .v-filterselect, .v-slider, .v-caption, .v-textfield';
  const items = [...w.querySelectorAll(ITEM_SEL)].map(el => {
    const cl = el.className;
    let kind = 'label';
    if (cl.includes('v-checkbox')) kind = 'checkbox';
    else if (cl.includes('v-filterselect')) kind = 'select';
    else if (cl.includes('v-slider')) kind = 'slider';
    else if (cl.includes('v-caption')) kind = 'caption';
    else if (cl.includes('v-textfield') && el.tagName === 'INPUT') kind = 'textfield';
    let value = '';
    if (kind === 'checkbox') {
      const inp = el.querySelector('input[type=checkbox]');
      value = inp ? String(inp.checked) : '';
    } else if (kind === 'select') {
      const inp = el.querySelector('.v-filterselect-input');
      value = inp ? norm(inp.value) : '';
      if (el.className.includes('v-disabled')) value += '  [disabled]';
    } else if (kind === 'slider') {
      const h = el.querySelector('.v-slider-handle');
      value = h ? (h.style.marginLeft || '') : '';
      if (el.className.includes('v-disabled')) value += '  [disabled]';
    } else if (kind === 'textfield') {
      value = norm(el.value);
    }
    const r = el.getBoundingClientRect();
    return { kind, text: norm(el.textContent).slice(0, 200), value,
             top: Math.round(r.top), left: Math.round(r.left) };
  });

  // for a known label: the control on its visual row, to its right. When
  // several sit on the row (e.g. "Hour to send message" has a $variable
  // <select> AND an unset "00:00" clock caption) prefer select > textfield
  // > slider > caption.
  const PREF = ['select', 'textfield', 'slider', 'caption'];
  const valueFor = (labelText) => {
    const li = items.findIndex(it => it.kind === 'label' && it.text.startsWith(labelText));
    if (li < 0) return null;
    const lab = items[li];
    const row = items.filter((it, j) => j !== li && PREF.includes(it.kind)
      && it.left >= lab.left - 5 && Math.abs(it.top - lab.top) <= 20);
    row.sort((a, b) => PREF.indexOf(a.kind) - PREF.indexOf(b.kind)
                    || Math.abs(a.top - lab.top) - Math.abs(b.top - lab.top));
    let best = row[0];
    if (!best) for (let j = li + 1; j < items.length; j++)
      if (PREF.includes(items[j].kind)) { best = items[j]; break; }
    return best ? { via: best.kind, value: best.value, text: best.text } : null;
  };

  const L = {
    comment: 'Comment:',
    ruleX: 'Rule [x]',
    termY: 'Comparison term [y]',
    storeResultVar: 'Store rule result to variable',
    messageGroup: 'Message group to send messages from',
    microDialogToStart: 'Micro dialog to start',
    hourToSendMessage: 'Hour to send message',
    notAnsweredTimeout: 'Minutes after sending until message is handled as not answered',
  };
  const fields = {};
  for (const [k, lbl] of Object.entries(L)) fields[k] = valueFor(lbl);

  const caps = items.filter(it => it.kind === 'caption').map(it => it.text);
  return {
    caption: norm((w.querySelector('.v-window-header') || {}).textContent),
    windowClasses: w.className,
    tabs: [...w.querySelectorAll('.v-tabsheet-tabitemcell')].map(e => norm(e.textContent)).filter(Boolean),
    checkboxes: items.filter(it => it.kind === 'checkbox')
      .map(it => ({ label: it.text, checked: it.value })),
    fields,
    sendHourClock: caps.find(c => /^\d{1,2}:\d{2}$/.test(c)) || null,
    notAnsweredText: caps.find(c => /\d+\s*days?,\s*\d+\s*hours?,\s*\d+\s*minutes?/i.test(c)) || null,
    innerTrees: [...w.querySelectorAll('.v-tree')].map(t =>
      [...t.querySelectorAll('.v-tree-node > .v-tree-node-caption')]
        .map(c => c.textContent.replace(/\s+/g, ' ').trim()).filter(Boolean)),
    allCaptions: caps,
    itemStream: items,
    html: w.outerHTML,
  };
}
"""

# section root -> short name
SECTION_ICON = {
    "calendar-icon-small.png": "DAILY BASIS",
    "watch-icon-small.png": "PERIODIC BASIS",
    "bubble-icon-small.png": "UNEXPECTED MESSAGE",
    "signs-icon-small.png": "USER INTENTION",
}


# ---------------------------------------------------------------------------
# tree navigation
# ---------------------------------------------------------------------------

async def ensure_rules_tree(page) -> bool:
    """True if the Rules `.v-tree` is on screen. If not, try clicking the
    in-app "Rules" tab once (a read-only nav) — the view drifts off it
    between runs. Returns False if it still isn't there."""
    if await page.evaluate("document.querySelectorAll('.v-tree').length"):
        return True
    tab = page.locator(".v-captiontext", has_text="Rules")
    if await tab.count():
        try:
            await tab.first.click()
            await page.wait_for_timeout(2500)
        except Exception:  # noqa: BLE001
            pass
    return bool(await page.evaluate("document.querySelectorAll('.v-tree').length"))


async def dump_tree(page) -> list[dict]:
    return await page.evaluate(TREE_DUMP_JS)


async def _aria_of(page, ti: int, i: int) -> str | None:
    trees = await page.evaluate(TREE_DUMP_JS)
    return next((n["ariaExpanded"] for n in trees[ti]["nodes"] if n["i"] == i), None)


async def select_node(page, ti: int, i: int) -> None:
    """Click a node's caption at x=20 to select it (box centre is dead space)."""
    cap = (page.locator(".v-tree").nth(ti)
           .locator(".v-tree-node[role=treeitem]").nth(i)
           .locator(":scope > .v-tree-node-caption"))
    await cap.click(position={"x": 20, "y": 8}, timeout=4000)


async def click_expander(page, ti: int, i: int) -> bool:
    """Expand the i-th treeitem; True if it is now aria-expanded=true."""
    for _ in range(2):
        try:
            await select_node(page, ti, i)
            await page.wait_for_timeout(600)
            await page.keyboard.press("ArrowRight")
            await page.wait_for_timeout(500)
        except Exception as e:  # noqa: BLE001
            print(f"    expand {ti}/{i}: {e!r}")
            return False
        if await _aria_of(page, ti, i) == "true":
            return True
    return False


async def liveness_ok(page) -> bool:
    """Expand the first visible collapsed node; catches an expired session
    (tree DOM stays, expand RPCs are dropped). A fully-expanded tree = live."""
    trees = await page.evaluate(TREE_DUMP_JS)
    collapsed = [n for n in trees[0]["nodes"]
                 if n["visible"] and n["ariaExpanded"] != "true"]
    if not collapsed:
        return True
    for n in collapsed:
        if await click_expander(page, 0, n["i"]):
            return True
    return False


async def expand_all(page, max_nodes: int = 400) -> dict:
    """Fully expand tree 0. One expansion per iteration, re-dumping each time
    (opening a node lazy-loads children and shifts later indices). A node that
    never reaches aria-expanded=true is a leaf."""
    tried: set[tuple] = set()
    leaves = expanded = 0
    for _ in range(max_nodes):
        trees = await page.evaluate(TREE_DUMP_JS)
        nxt = next(((n["i"], (n["depth"], n["caption"]))
                    for n in trees[0]["nodes"]
                    if n["visible"] and n["ariaExpanded"] != "true" and n["caption"]
                    and (n["depth"], n["caption"]) not in tried), None)
        if nxt is None:
            break
        i, key = nxt
        tried.add(key)
        if await click_expander(page, 0, i):
            expanded += 1
        else:
            leaves += 1
        if (expanded + leaves) % 15 == 0:
            print(f"  ... {expanded} expanded / {leaves} leaves")
    trees = await page.evaluate(TREE_DUMP_JS)
    return {
        "expandedNodes": sum(1 for n in trees[0]["nodes"] if n["ariaExpanded"] == "true"),
        "leafNodes": leaves,
        "emptyRoots": [n["caption"] for n in trees[0]["nodes"]
                       if n["depth"] == 0 and n["ariaExpanded"] != "true"],
        "nodeCount": trees[0]["nodeCount"],
    }


def parent_chain(nodes: list[dict], idx: int) -> list[str]:
    """Caption chain from the section root down to (not incl.) node idx."""
    chain: list[str] = []
    want = nodes[idx]["depth"] - 1
    for j in range(idx - 1, -1, -1):
        if nodes[j]["depth"] == want:
            chain.insert(0, nodes[j]["caption"])
            want -= 1
            if want < 0:
                break
    return chain


# ---------------------------------------------------------------------------
# "Edit rule:" modal
# ---------------------------------------------------------------------------

async def rule_edit_button(page):
    handles = await page.evaluate_handle(
        """() => [...document.querySelectorAll('.v-button')].filter(bt => {
        const cap = (bt.querySelector('.v-button-caption')||{}).textContent||'';
        return cap.trim() === 'Edit';
      })""")
    props = await handles.get_properties()
    for _, h in props.items():
        el = h.as_element()
        if el and await el.is_visible():
            return el
    return None


async def close_windows(page) -> int:
    """Dismiss every open modal. On the rule editor the only button ("Close")
    commits a no-op re-save — returns how many such committing clicks."""
    committed = 0
    for _ in range(6):
        if not await page.locator(".v-window").count():
            return committed
        clicked = False
        for label in ("Cancel", "Close", "Exit", "OK"):
            btn = page.locator(".v-window .v-button-caption", has_text=label)
            if await btn.count():
                await btn.last.click()
                if label in ("Close", "OK"):
                    committed += 1
                clicked = True
                break
        if not clicked:
            await page.keyboard.press("Escape")
        await page.wait_for_timeout(450)
    return committed


async def open_rule_modal(page, ti: int, i: int) -> dict | None:
    """Select the i-th treeitem, click its toolbar Edit, return the
    RULE_MODAL_JS dump plus the DOES-NOT-answer inner trees. Retries once.
    Leaves the modal OPEN — caller must close_windows()."""
    for attempt in range(2):
        await select_node(page, ti, i)
        await page.wait_for_timeout(450)
        btn = await rule_edit_button(page)
        if not btn:
            await page.wait_for_timeout(500)
            continue
        await btn.click()
        try:
            await page.wait_for_selector(".v-window .v-window-header", timeout=6000)
        except Exception:  # noqa: BLE001
            pass
        await page.wait_for_timeout(900)
        dump = await page.evaluate(RULE_MODAL_JS)
        if dump.get("caption"):
            does_not = None
            tab = page.locator(".v-window .v-tabsheet-tabitemcell",
                               has_text="DOES NOT answer")
            if await tab.count():
                try:
                    await tab.first.click()
                    await page.wait_for_timeout(500)
                    does_not = await page.evaluate(
                        "() => [...document.querySelectorAll('.v-window .v-tree')]"
                        ".map(t => [...t.querySelectorAll('.v-tree-node > "
                        ".v-tree-node-caption')].map(c => c.textContent.trim()))")
                except Exception:  # noqa: BLE001
                    pass
            dump["doesNotAnswerInnerTrees"] = does_not
            return dump
        await close_windows(page)
        await page.wait_for_timeout(600)
    return None


# ---------------------------------------------------------------------------
# field parsing (pure)
# ---------------------------------------------------------------------------

_ACTIONS = {
    "Send message if rule result is TRUE": "send_message",
    "Start micro dialog if rule result is TRUE": "start_micro_dialog",
    "Mark case as solved (unexpected message) and stop the current rule execution run if result is TRUE": "mark_solved_stop_run",
    "Stop current rule execution run and finish coaching for this participant if rule result is TRUE": "stop_run_finish_coaching",
}
_DISABLED = "  [disabled]"
# a Vaadin default that means "not set" for the dialog / hour selects
_UNSET_SELECT = {"$participantNextMicroDialogIdentifier"}


def _clean_select(fv: dict | None) -> str | None:
    if not fv:
        return None
    v = (fv.get("value") or "").replace(_DISABLED, "").strip()
    if not v or _DISABLED.strip() in v or v in _UNSET_SELECT:
        return None
    return v


def _timeout_minutes(text: str | None) -> int | None:
    if not text:
        return None
    m = re.search(r"(\d+)\s*days?,\s*(\d+)\s*hours?,\s*(\d+)\s*minutes?", text, re.I)
    if not m:
        return None
    d, h, mi = (int(x) for x in m.groups())
    return d * 1440 + h * 60 + mi


def _flatten_inner(trees) -> list[str]:
    """innerTrees comes as [[caption, ...]] (current JS) or [{nodes:[...]}]
    (older dumps). Return a flat list of captions either way."""
    out: list[str] = []
    for t in trees or []:
        if isinstance(t, dict):
            out += [c for c in t.get("nodes", []) if c]
        elif isinstance(t, (list, tuple)):
            out += [c for c in t if c]
    return out


def _hour_from_itemstream(dump: dict) -> str | None:
    """Fallback: read the 'Hour to send message' row's <select> straight from
    the item stream (the row-matching in RULE_MODAL_JS can pick the adjacent
    unset '00:00' caption instead of the $variable select)."""
    items = dump.get("itemStream") or []
    li = next((k for k, it in enumerate(items)
               if it["kind"] == "label"
               and it["text"].startswith("Hour to send message")), None)
    if li is None:
        return None
    lab = items[li]
    sels = [it for it in items if it["kind"] == "select"
            and it["left"] >= lab["left"] - 5
            and abs(it["top"] - lab["top"]) <= 20]
    return sels[0]["value"] if sels else None


def parse_rule_fields(dump: dict) -> dict:
    """RULE_MODAL_JS dump -> the clean Stage-3 record for one sending rule."""
    f = dump.get("fields", {}) or {}
    cbs = {c["label"]: c["checked"] == "true" for c in dump.get("checkboxes", [])}
    actions = [name for lbl, name in _ACTIONS.items() if cbs.get(lbl)]
    hour = _clean_select(f.get("hourToSendMessage"))
    if not hour or not hour.startswith("$"):
        hour = _clean_select({"value": _hour_from_itemstream(dump) or ""}) or hour
    return {
        "comment": (f.get("comment") or {}).get("value") or None,
        "ruleExpr": " ".join(x for x in (
            (f.get("ruleX") or {}).get("value"),
            (f.get("termY") or {}).get("value")) if x and x != "(no value set)") or None,
        "actions": actions,
        "primaryAction": actions[0] if actions else None,
        "microDialogToStart": _clean_select(f.get("microDialogToStart")),
        "microDialogPath": (_clean_select(f.get("microDialogToStart")) or "").split(" > ") or None,
        "messageGroup": _clean_select(f.get("messageGroup")),
        "sendHourVariable": hour if (hour or "").startswith("$") else None,
        "sendHourLiteral": None if (hour or "").startswith("$") else hour,
        "sendHourClock": dump.get("sendHourClock"),
        "notAnsweredTimeoutMinutes": _timeout_minutes(dump.get("notAnsweredText")),
        "notAnsweredTimeoutText": dump.get("notAnsweredText"),
        "storeResultVariable": _clean_select(f.get("storeResultVar")),
        "doesAnswerRules": _flatten_inner(dump.get("innerTrees")),
        "doesNotAnswerRules": _flatten_inner(dump.get("doesNotAnswerInnerTrees")),
        "modalCaption": dump.get("caption"),
    }
