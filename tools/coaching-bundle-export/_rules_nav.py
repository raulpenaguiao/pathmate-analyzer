"""Shared toolkit for the PMCP **Rules tab** (a Vaadin 7 `.v-tree`).

Used by `probe_rules_tree.py` (discovery) and `export_coaching.py` (the export).
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
import sys
from pathlib import Path

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
SENDER_ICON = "message-icon-small.png"       # rule sends a message / starts a dialog
CONDITION_ICON = "rule-icon-small.png"       # condition / calculation rule


def _parse_rule_caption(caption: str) -> dict:
    """Structured `{comment, kind, lhs, rhs/target, ...}` from a Rules-tree
    caption (`"<comment>: <expr>"`, comment optional) - Stage 4 Phase 0
    (`docs/stage4_chat_engine_plan.md`). Delegates to the shared grammar in
    `app/rule_grammar.py` so the exporter and the HTML-driven simulator
    parse the same fixed operator phrases from one place; see that module's
    docstring for why comment-splitting has to happen here rather than in
    `parse_expr` itself (the HTML export never has a comment prefix to
    strip - it's already a separate column there)."""
    repo = Path(__file__).resolve().parents[2]
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))
    from app.rule_grammar import parse_rule_caption
    return parse_rule_caption(caption)


def build_rule_tree(tree_nodes: list[dict]) -> list[dict]:
    """A flat, ordered rule list with stable uids + parent links, from a
    TREE_DUMP_JS node list. Section roots (depth 0) set the `section` of
    everything under them and are dropped from the output. Each node also
    gets an `expr` field: the caption's comment + structured expression
    (Stage 4 Phase 0) - `expr.kind` is "unsupported" for JS-snippet/regex
    conditions PMCP allows outside its declarative mini-language."""
    out: list[dict] = []
    last_at_depth: dict[int, str | None] = {}
    section = None
    counter = 0
    for n in tree_nodes:
        d = n["depth"]
        if d == 0:
            section = SECTION_ICON.get(n["icon"], n["caption"])
            last_at_depth = {0: None}
            continue
        uid = f"r-{counter:03d}"
        counter += 1
        kind = ("sender" if SENDER_ICON in n["icon"]
                else "condition" if CONDITION_ICON in n["icon"] else "other")
        out.append({
            "uid": uid, "section": section, "depth": d, "order": counter,
            "parentUid": last_at_depth.get(d - 1),
            "kind": kind, "icon": n["icon"], "caption": n["caption"],
            "expr": _parse_rule_caption(n["caption"]),
            "treeIndex": n["i"],
        })
        last_at_depth[d] = uid
        for deeper in [k for k in last_at_depth if k > d]:
            del last_at_depth[deeper]
    return out


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
            await tab.first.click(timeout=8000)
        except Exception:  # noqa: BLE001
            await _mouse_click(page, tab.first)
        await page.wait_for_timeout(2500)
    return bool(await page.evaluate("document.querySelectorAll('.v-tree').length"))


async def dump_tree(page) -> list[dict]:
    return await page.evaluate(TREE_DUMP_JS)


async def _aria_of(page, ti: int, i: int) -> str | None:
    trees = await page.evaluate(TREE_DUMP_JS)
    return next((n["ariaExpanded"] for n in trees[ti]["nodes"] if n["i"] == i), None)


async def _mouse_click(page, locator, offset_x: float = None, offset_y: float = None,
                        timeout: int = 8000) -> bool:
    """Click via a real OS-level mouse move+click at the element's actual
    on-screen coordinates, instead of Playwright's Locator.click() (which
    does its own "visible, enabled, stable" actionability re-check).
    Confirmed live 2026-09-15: that re-check can fail persistently (full
    default-timeout hangs, `expand_all`/`select_node`/tab navigation all
    affected at once) with NO modal, notification, or overlay present to
    explain it - not the well-documented "not enabled" quirk (which is a
    real disabled state), something else about Vaadin's DOM causing
    Playwright's stability check specifically to never settle. A raw mouse
    click at the same coordinates goes through the real input pipeline
    (unlike a JS `element.click()`, which can desync the Vaadin
    client/server session if used to bypass a stuck popup - confirmed
    2026-09-14, see `create_variables.py`/memory) and worked every time
    this was hit. Returns False (not an exception) if the element can't be
    located at all, so callers can fall back or retry."""
    try:
        await locator.scroll_into_view_if_needed(timeout=timeout)
    except Exception:  # noqa: BLE001
        pass  # bounding_box below still catches a genuinely-missing element
    try:
        box = await locator.bounding_box(timeout=timeout)
    except Exception:  # noqa: BLE001
        return False
    if not box:
        return False
    x = box["x"] + (offset_x if offset_x is not None else box["width"] / 2)
    y = box["y"] + (offset_y if offset_y is not None else box["height"] / 2)
    await page.mouse.move(x, y)
    await page.wait_for_timeout(120)
    await page.mouse.click(x, y)
    return True


class WrongMenuError(RuntimeError):
    """Raised when the Rules `.v-tree` isn't on screen and couldn't be
    switched to. Without this check, navigating from the wrong tab surfaces
    as a confusing element-not-found/timeout deep inside select_node rather
    than a clear "wrong tab" message - see _menu_nav.WrongMenuError, the
    same class of mistake found live 2026-09-18 in a Micro Dialogs script."""


async def _require_rules_tree(page) -> None:
    """select_node() is the one primitive every Rules-tab navigation
    function (click_expander, expand_all, open_rule_modal, ...) goes
    through, so checking here covers all of them unconditionally - no
    caller can skip it by forgetting to call ensure_rules_tree() itself."""
    if not await ensure_rules_tree(page):
        raise WrongMenuError(
            "Rules tree not on screen and couldn't switch to it - check the "
            "browser is actually in a coaching's Edit view (not the "
            "Coachings list or a different tab like Micro Dialogs/Variables).")


async def select_node(page, ti: int, i: int) -> None:
    """Click a node's caption at x=20 to select it (box centre is dead space)."""
    await _require_rules_tree(page)
    cap = (page.locator(".v-tree").nth(ti)
           .locator(".v-tree-node[role=treeitem]").nth(i)
           .locator(":scope > .v-tree-node-caption"))
    try:
        await cap.click(position={"x": 20, "y": 8}, timeout=4000)
    except Exception:  # noqa: BLE001
        if not await _mouse_click(page, cap, offset_x=20, offset_y=8):
            raise


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
    commits a no-op re-save — returns how many such committing clicks.

    The dismiss button intermittently reports "not enabled" for well over
    Playwright's default 30s actionability wait (a known Vaadin quirk,
    documented repeatedly across autochanges/ — not just the usual
    millisecond-scale flakiness). A single `.click()` with no outer retry
    then aborts the whole caller with an unhandled TimeoutError, which is
    exactly what crashed export_coaching.py mid-sweep on 2026-09-12 (see
    autochanges/2026-09-12-alex-v02-phase3.7-*). Retrying the click itself a
    few times (4x8s) fixed that occurrence, but a second run the same day hit
    an even longer stuck spell that exhausted all 4 retries too — so a failed
    click no longer raises here: fall back to Escape and let the OUTER loop
    (widened 6->10) re-examine and retry the whole close, rather than
    crashing the caller's sweep over one bad spell. Only raise if a modal is
    still open after every outer attempt — fail loud instead of silently
    returning with a modal left open, which would desync the caller's
    per-sender loop."""
    committed = 0
    for _ in range(10):
        if not await page.locator(".v-window").count():
            return committed
        clicked = False
        for label in ("Cancel", "Close", "Exit", "OK"):
            btn = page.locator(".v-window .v-button-caption", has_text=label)
            if await btn.count():
                ok = False
                for attempt in range(4):
                    try:
                        await btn.last.click(timeout=8000)
                        ok = True
                        break
                    except Exception:  # noqa: BLE001
                        if attempt == 3:
                            ok = await _mouse_click(page, btn.last)
                            break
                        await page.wait_for_timeout(1000)
                if ok:
                    if label in ("Close", "OK"):
                        committed += 1
                else:
                    print(f"  ! close_windows: {label!r} stuck 'not enabled' "
                          f"past 4x8s — Escape + outer retry")
                    await page.keyboard.press("Escape")
                clicked = True
                break
        if not clicked:
            await page.keyboard.press("Escape")
        await page.wait_for_timeout(450)
    if await page.locator(".v-window").count():
        raise RuntimeError("close_windows: a modal is still open after 10 "
                           "attempts (dismiss button stuck 'not enabled') — "
                           "failing loud rather than leaving state open.")
    return committed


async def open_rule_modal(page, ti: int, i: int) -> dict | None:
    """Select the i-th treeitem, click its toolbar Edit, return the
    RULE_MODAL_JS dump plus the DOES-NOT-answer inner trees. Retries a few
    times. Leaves the modal OPEN — caller must close_windows()."""
    for attempt in range(4):
        try:
            await select_node(page, ti, i)
        except Exception:  # noqa: BLE001
            await page.wait_for_timeout(800)
            continue
        await page.wait_for_timeout(450)
        btn = await rule_edit_button(page)
        if not btn:
            await page.wait_for_timeout(500)
            continue
        try:
            await btn.click(timeout=8000)
        except Exception:  # noqa: BLE001
            # same "element not enabled" Vaadin quirk close_windows() retries
            # for — a fresh select_node + re-fetched button on the next loop
            # iteration is what actually clears it, not just waiting longer.
            # On the last attempt, try a real mouse click before giving up
            # entirely (see _mouse_click's docstring — confirmed live
            # 2026-09-15 this clears cases plain retrying never does).
            if attempt == 3 and await _mouse_click(page, btn):
                pass
            else:
                await page.wait_for_timeout(800)
                continue
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
# write helpers (Phase 1 of the ALEX v02 redesign, docs/ALEX_v02_redesign_spec.md)
#
# Confirmed live 2026-09-11 (autochanges/2026-09-11-alex-v02-phase1-completion.md):
#   - Comment / Rule[x] / Term[y] / result-variable each open a simple
#     Cancel/OK popup (type + OK = a real commit, verified via the tree
#     caption after close_windows()).
#   - The 4 TRUE-result action checkboxes are directly clickable in the
#     outer "Edit rule:" form, no popup needed.
#   - "Hour to send message" is a live $variable filterselect IF its owning
#     action checkbox is already checked - pick a value from its dropdown
#     directly, no popup.
#   - The not-answered-timeout slider/quick-picks are NOT settable through
#     any path found this session - deliberately no write function for it
#     here. Don't add one without a fresh discovery pass.
#   - The modal must already be open (open_rule_modal). None of these
#     commit on their own except by calling close_windows() afterward -
#     "Close" on an already-EXISTING rule's Edit form is a real commit
#     (same as every read-only open); on a "Create rule:" form "Close" ALSO
#     commits (creates the rule) - there is no separate Cancel on either.
# ---------------------------------------------------------------------------

async def _click_retry(page, locator, attempts: int = 4, timeout: int = 8000,
                        settle_ms: int = 1000) -> bool:
    """Retry a click a few times before giving up - the "element is not
    enabled" Vaadin quirk (documented repeatedly across this project) can
    persist for the full default 30s actionability wait. Confirmed live
    2026-09-14/15: `_open_field_popup`/`_fill_and_ok` had never had this
    protection (unlike `close_windows`/`open_rule_modal`, hardened earlier)
    and crashed mid Phase-4.1.2 rule edit on this exact flakiness, leaving
    two stacked stuck popups open.

    After real retries are exhausted, falls back to a raw OS-level mouse
    click (`_mouse_click`) at the element's actual coordinates before
    giving up entirely. This is NOT the same as forcing a click via a raw
    JS `element.click()` - that bypasses the real input pipeline and was
    confirmed live (2026-09-14, `create_variables.py`) to be able to
    visually close a popup while desyncing the Vaadin client/server
    session, silently breaking every later server round-trip with no
    error shown - never do that. A real `page.mouse.move()+click()` at the
    genuine coordinates goes through the same event pipeline a human
    click would; it only skips Playwright's own extra "stable across two
    frames" pre-check, which was confirmed live 2026-09-15 to hang
    indefinitely on elements with no modal/overlay/notification present to
    explain it (session-wide - `expand_all`, `select_node`, and plain tab
    navigation were all affected at once, ruling out the ordinary
    "not enabled" disabled-state quirk this function was originally
    written for)."""
    for attempt in range(attempts):
        try:
            await locator.click(timeout=timeout)
            return True
        except Exception:  # noqa: BLE001
            if attempt == attempts - 1:
                return await _mouse_click(page, locator)
            await page.wait_for_timeout(settle_ms)
    return False


async def _open_field_popup(page, edit_index: int):
    """Click the edit_index-th 'Edit' button in the OUTER (first) .v-window,
    in DOM order. Leaves the resulting popup open."""
    handle = await page.evaluate_handle(
        """(n) => {
          const wins = [...document.querySelectorAll('.v-window')];
          const w = wins[0];
          if (!w) return null;
          const edits = [...w.querySelectorAll('.v-button')].filter(bt =>
            ((bt.querySelector('.v-button-caption')||{}).textContent||'').trim() === 'Edit');
          return edits[n] || null;
        }""",
        edit_index,
    )
    el = handle.as_element() if handle else None
    if not el:
        return False
    if not await _click_retry(page, el):
        return False
    await page.wait_for_timeout(900)
    return True


async def _fill_and_ok(page, text: str) -> bool:
    """The just-opened popup: fill its single textarea/input, click OK."""
    sub = page.locator(".v-window").last
    ta = sub.locator("textarea, input[type=text]").first
    if not await ta.count():
        return False
    if not await _click_retry(page, ta):
        return False
    await ta.fill(text)
    ok = sub.locator(".v-button-caption", has_text="OK").last
    if not await ok.count():
        return False
    if not await _click_retry(page, ok):
        return False
    await page.wait_for_timeout(700)
    return True


async def set_rule_comment(page, text: str) -> bool:
    """Modal must already be open (open_rule_modal). Edit index 0."""
    return await _open_field_popup(page, 0) and await _fill_and_ok(page, text)


async def set_rule_condition_x(page, expr: str) -> bool:
    """The 'Rule [x] (with placeholders)' condition expression. Edit index 1."""
    return await _open_field_popup(page, 1) and await _fill_and_ok(page, expr)


async def set_rule_condition_y(page, expr: str) -> bool:
    """The 'Comparison term [y] (with placeholders)' expression. Edit index 2."""
    return await _open_field_popup(page, 2) and await _fill_and_ok(page, expr)


async def set_rule_result_variable(page, var_name: str) -> bool:
    """'Store rule result to variable'. Edit index 3. var_name should
    already exist (create it first via create_variables.py) - this popup's
    'Existing variables to select' list is for convenience, typing a new
    name directly is also possible but untested here."""
    return await _open_field_popup(page, 3) and await _fill_and_ok(page, var_name)


async def set_rule_operator(page, operator_text: str, verify: bool = True) -> bool:
    """The comparison/assign OPERATOR (e.g. "calculated value is smaller
    than", "calculate value but result is always true") is a SEPARATE
    control from Rule[x]/Term[y] - confirmed live 2026-09-15 building
    Phase 4.1's medication rules. It's not behind one of the 4 Edit-button
    popups; it's a directly-clickable `.v-filterselect` (Vaadin ComboBox,
    `-no-input` variant - click-to-open-a-list, not type-to-filter) sitting
    in the OUTER form, the first non-disabled one in DOM order. On an
    EXISTING rule (e.g. one made via Duplicate) this already holds the
    right value and never needs touching - `set_rule_condition_x`/`_y`
    only ever change the bare value/variable text, never the operator
    phrase, and that's correct: editing Rule[x] on a duplicated cmp-type
    rule does not change it into an assign-type rule or vice versa. Only a
    brand-new rule (via `New`) starts with a DEFAULT operator
    ("calculated value equals", confirmed live) that must be set
    explicitly before the rule means what you intend.

    Confirmed unreliable enough to need its own verification: one live
    click on the filterselect + option can report success (no exception)
    while the selection silently doesn't take, leaving the rule on
    PMCP's default placeholder display (`--- calculated value equals
    ---`) - the same class of "click succeeds, intent doesn't land"
    flakiness documented elsewhere in this project (e.g. checkboxes
    needing `force=True`). `verify=True` (default) re-reads the
    filterselect's displayed text after selecting and retries once if it
    doesn't match - don't disable this without a good reason."""
    for attempt in range(2 if verify else 1):
        w = page.locator(".v-window").first
        fs = w.locator(".v-filterselect:not(.v-disabled)").first
        if not await _click_retry(page, fs):
            continue
        await page.wait_for_timeout(500)
        popup = page.locator(".v-filterselect-suggestpopup")
        if not await popup.count():
            continue
        opt = popup.get_by_text(operator_text, exact=False).first
        if not await opt.count():
            return False  # the text itself doesn't exist as an option - retrying won't help
        if not await _click_retry(page, opt):
            continue
        await page.wait_for_timeout(500)
        if not verify:
            return True
        now = await fs.inner_text() if await fs.count() else ""
        if operator_text in now:
            return True
    return False


async def set_rule_micro_dialog(page, path_text: str, max_pages: int = 20) -> bool:
    """'Micro dialog to start' - the 3rd filterselect (index 2) in the outer
    form, same `-no-input` click-to-open-a-list widget as the operator
    dropdown, but server-paginated (confirmed live 2026-09-15: 10 options
    per page, `.v-filterselect-nextpage`/`-prevpage` controls) rather than
    a short fixed list, since it lists every dialog AND folder in the whole
    coaching. `path_text` should match a full path exactly as PMCP renders
    it - `"A > B"` for a dialog nested under folder A (confirmed live,
    Phase 3.5: a dialog nested under its original gets listed as a path,
    not a bare name)."""
    w = page.locator(".v-window").first
    fs = w.locator(".v-filterselect").nth(2)
    if not await _click_retry(page, fs):
        return False
    await page.wait_for_timeout(600)
    popup = page.locator(".v-filterselect-suggestpopup")
    if not await popup.count():
        return False
    for _ in range(max_pages):
        opt = popup.get_by_text(path_text, exact=True)
        if await opt.count():
            if not await _click_retry(page, opt.first):
                return False
            await page.wait_for_timeout(500)
            now = await fs.inner_text()
            return path_text in now
        nextbtn = popup.locator(".v-filterselect-nextpage")
        if not await nextbtn.count():
            return False
        cls = await nextbtn.get_attribute("class") or ""
        if "disabled" in cls:
            return False
        await _click_retry(page, nextbtn)
        await page.wait_for_timeout(500)
    return False


async def set_rule_checkbox(page, label_substr: str, checked: bool) -> bool:
    """One of the 4 TRUE-result action checkboxes (or any other directly-
    live checkbox in the outer form). Modal must already be open. No-ops if
    already in the desired state."""
    cb = page.locator(".v-window .v-checkbox", has_text=label_substr).first
    if not await cb.count():
        return False
    inp = cb.locator("input[type=checkbox]")
    now = await inp.is_checked()
    if now != checked:
        await inp.click()
        await page.wait_for_timeout(400)
    return True


async def set_rule_hour_variable(page, var_name: str, verify: bool = True,
                                  max_pages: int = 40) -> bool:
    """The 'Hour to send message' $variable filterselect. Only live once
    its owning action checkbox (Send message / Start micro dialog) is
    already checked - call set_rule_checkbox first if needed. var_name
    without the leading '$' also works (matched as substring).

    Rewritten 2026-09-16: (1) to match `set_rule_operator`/
    `set_rule_micro_dialog`'s proven approach (click the filterselect
    WRAPPER directly via `_click_retry`, find the option by text in the
    popup) - the original version clicked an inner `<input>` and looked
    for `.gwt-MenuItem`, which doesn't match this widget's actual popup
    markup and silently always returned False; (2) because this list is
    every $variable in the coaching (334 on ALEX v01) and is server-
    paginated the same way `set_rule_micro_dialog`'s dialog-path list is -
    a variable past the first ~10 alphabetically needs paging to reach,
    confirmed live with `$userSetDesired...` (near the end of the
    alphabet)."""
    # the Hour filterselect is identified by position (4th, index 3) per
    # the confirmed field order - see phase1-completion.md's table.
    fs = page.locator(".v-window .v-filterselect").nth(3)
    if not await _click_retry(page, fs):
        return False
    await page.wait_for_timeout(600)
    popup = page.locator(".v-filterselect-suggestpopup")
    if not await popup.count():
        return False
    for _ in range(max_pages):
        opt = popup.get_by_text(var_name, exact=False).first
        if await opt.count():
            if not await _click_retry(page, opt):
                return False
            await page.wait_for_timeout(500)
            if not verify:
                return True
            now = await fs.inner_text() if await fs.count() else ""
            return var_name.lstrip("$") in now
        nextbtn = popup.locator(".v-filterselect-nextpage")
        if not await nextbtn.count():
            break
        cls = await nextbtn.get_attribute("class") or ""
        if "disabled" in cls:
            break
        await _click_retry(page, nextbtn)
        await page.wait_for_timeout(500)
    await page.keyboard.press("Escape")
    return False


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
