import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

OUT = Path("docs/screenshots")
OUT.mkdir(parents=True, exist_ok=True)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        await page.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        await page.wait_for_timeout(800)
        split = page.locator(".split-panels")
        await split.scroll_into_view_if_needed()
        await page.wait_for_timeout(300)
        await split.screenshot(path=str(OUT / "ai-assistant-panel.png"))
        await page.screenshot(path=str(OUT / "dashboard-overview.png"), full_page=True)
        await browser.close()

asyncio.run(main())
print("saved", list(OUT.glob("*.png")))
