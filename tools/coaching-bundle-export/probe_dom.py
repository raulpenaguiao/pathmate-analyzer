"""Connect to the persistent Chromium over CDP and report the DOM structure of
whatever is currently on screen, so we can pin down the real selectors for the
micro-dialog menubar and the message table. Non-destructive: reads + screenshot.

Run:  PMCP_CDP=http://127.0.0.1:9222 .venv/bin/python scratchpad/pmcp_probe.py
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from playwright.async_api import async_playwright

HERE = Path(__file__).resolve().parent
CDP = os.environ.get("PMCP_CDP", "http://127.0.0.1:9222")

PROBE_JS = r"""
() => {
  const uniq = (a) => [...new Set(a)];
  const classesMatching = (re) => uniq(
    [...document.querySelectorAll('*')]
      .flatMap(e => [...e.classList])
      .filter(c => re.test(c))
  );
  const sel = (s) => document.querySelectorAll(s).length;
  const sample = (s, n=3) => [...document.querySelectorAll(s)].slice(0, n)
    .map(e => (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 60));
  return {
    url: location.href,
    title: document.title,
    menuish_classes: classesMatching(/menu|md-|dialog|nav/i).slice(0, 60),
    tableish_classes: classesMatching(/table|grid/i).slice(0, 40),
    counts: {
      'v-menubar': sel('.v-menubar'),
      'v-menubar-menuitem': sel('.v-menubar-menuitem'),
      '.md-menu': sel('.md-menu'),
      '.v-slot-md-menu': sel('.v-slot-md-menu'),
      'v-table': sel('.v-table'),
      'v-table-body tr': sel('.v-table .v-table-body tr'),
      'v-grid': sel('.v-grid'),
      'v-grid-row': sel('.v-grid-row'),
      'v-tree': sel('.v-tree'),
      'v-tree-node': sel('.v-tree-node'),
      'iframe': sel('iframe'),
    },
    menubar_sample: sample('.v-menubar-menuitem', 12),
    table_headers: [...document.querySelectorAll(
      '.v-table .v-table-header-cell .v-table-caption-container, .v-grid-column-header-content')]
      .map(e => e.textContent.trim()),
    first_menuitem_html: (document.querySelector('.v-menubar-menuitem') || {}).outerHTML || null,
    body_class: document.body.className,
  };
}
"""


async def main() -> None:
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp(CDP)
        print(f"contexts: {len(browser.contexts)}")
        report = []
        for ci, ctx in enumerate(browser.contexts):
            for pi, page in enumerate(ctx.pages):
                try:
                    url = page.url
                except Exception:
                    url = "?"
                frames = page.frames
                entry = {"ctx": ci, "page": pi, "url": url,
                         "frames": len(frames), "results": []}
                for fi, fr in enumerate(frames):
                    try:
                        r = await fr.evaluate(PROBE_JS)
                        r["_frame_index"] = fi
                        r["_frame_url"] = fr.url
                        entry["results"].append(r)
                    except Exception as e:  # noqa: BLE001
                        entry["results"].append({"_frame_index": fi,
                                                 "_frame_url": fr.url,
                                                 "error": repr(e)})
                report.append(entry)
                # screenshot the top page only
                try:
                    shot = HERE / f"probe_ctx{ci}_pg{pi}.png"
                    await page.screenshot(path=str(shot), full_page=False)
                    entry["screenshot"] = str(shot)
                except Exception as e:  # noqa: BLE001
                    entry["screenshot_error"] = repr(e)

        out = HERE / "probe.json"
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        print(f"wrote {out}")
        for e in report:
            print(f"\n== ctx{e['ctx']} page{e['page']}  {e['url']}  "
                  f"({e['frames']} frames)")
            for r in e["results"]:
                if "error" in r:
                    print(f"   frame {r['_frame_index']} {r['_frame_url']}: "
                          f"ERR {r['error']}")
                    continue
                c = r["counts"]
                hot = {k: v for k, v in c.items() if v}
                print(f"   frame {r['_frame_index']} {r['_frame_url'][:70]}")
                print(f"     nonzero: {hot}")
                if r["table_headers"]:
                    print(f"     headers: {r['table_headers']}")
                if r["menubar_sample"]:
                    print(f"     menu: {r['menubar_sample']}")


if __name__ == "__main__":
    asyncio.run(main())
