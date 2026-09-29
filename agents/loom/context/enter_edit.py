import asyncio, sys
sys.path.insert(0, "/home/raul/projects/pathmate-analyzer/tools/coaching-bundle-export")
from playwright.async_api import async_playwright
import _report_fetch as RF
import _menu_nav as S

NAME = "ALEX v01 zum Ausprobieren"
LOGGED_IN = """() => !document.querySelector('input[type=password]')
  && ![...document.querySelectorAll('.v-Notification')].some(n => /session expired/i.test(n.textContent||''))
  && /Logout/.test(document.body.innerText)"""

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.connect_over_cdp("http://127.0.0.1:9222")
        ctx = b.contexts[0]
        live = [p for p in ctx.pages if await p.evaluate(LOGGED_IN)]
        print("tabs:", len(ctx.pages), "logged in:", len(live))
        if not live:
            sys.exit("no logged-in tab")
        page = live[0]
        # close the dead login tabs so apply's pick_page can't land on one
        for p in ctx.pages:
            if p is not page:
                await p.close()
        await page.bring_to_front()
        await S.neutralize_tooltips(page)
        await page.locator(".v-menubar-menuitem-caption, .v-button-caption, span",
                           has_text="Coachings").first.click()
        await page.wait_for_timeout(2000)
        ok = await RF.enter_edit_view(page, NAME)
        print("edit view:", ok)
        print("micro dialogs:", await S.ensure_micro_dialogs(page))

asyncio.run(main())
