"""Desktop/mobile smoke and navigation checks against a running seeded server."""

import os
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
BASE = os.getenv("BROWSER_BASE_URL", "http://127.0.0.1:8000")
PASSWORD = os.environ["DEMO_PASSWORD"]
OUT = ROOT / "test-results"
OUT.mkdir(exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chromium")
    page = browser.new_page(viewport={"width": 1440, "height": 1100}, device_scale_factor=1)
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    response = page.goto(BASE)
    assert response.status == 200
    expect(page.get_by_role("link", name="Get started").first).to_be_visible()
    page.screenshot(path=str(OUT / "landing-desktop.png"), full_page=True)
    page.goto(BASE + "/login/")
    page.locator("#id_username").fill("demo@finpilot.local")
    page.locator("#id_password").fill(PASSWORD)
    page.get_by_role("button", name="Sign in").click()
    page.wait_for_url("**/b/*/")
    expect(page.locator("h1")).to_contain_text("Financial Survival Overview")
    expect(page.locator("#survivalChart")).to_be_visible()
    page.screenshot(path=str(OUT / "dashboard-desktop.png"), full_page=True)
    origin = page.url
    for label in ["My Business", "AI Advisor", "Financial Planning", "Reports", "Dashboard"]:
        page.get_by_role("navigation", name="Main navigation").get_by_role("link", name=label, exact=True).click()
        assert page.locator("h1").count() == 1
    page.locator(".switcher summary").click()
    buttons = page.locator(".switcher .dropdown button")
    if buttons.count() > 1:
        buttons.nth(1).click()
        assert page.url != origin
    for size in [{"width": 390, "height": 844}, {"width": 768, "height": 1024}]:
        page.set_viewport_size(size)
        page.goto(BASE + "/workspace/")
        expect(page.locator("h1")).to_be_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), "Dashboard has horizontal overflow"
        page.screenshot(path=str(OUT / f"dashboard-{size['width']}.png"), full_page=True)
        for label in ["My Business", "AI Advisor", "Financial Planning", "Reports"]:
            page.get_by_role("navigation", name="Main navigation").get_by_role("link", name=label, exact=True).click()
            expect(page.locator("h1")).to_be_visible()
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), f"{label} has horizontal overflow"
    assert not errors, errors
    browser.close()
print("Browser checks passed: desktop, mobile, tablet, five-page navigation, business switching, no page errors.")
