"""Verify private operator-provisioned credentials without printing or recording them."""

import argparse
from pathlib import Path

from dotenv import dotenv_values
from playwright.sync_api import sync_playwright, expect

parser = argparse.ArgumentParser()
parser.add_argument("url")
args = parser.parse_args()
base = args.url.rstrip("/")
values = dotenv_values(Path(__file__).resolve().parent.parent / ".env")
email = values.get("LIVE_LOGIN_EMAIL")
password = values.get("LIVE_LOGIN_PASSWORD")
if not email or not password:
    raise SystemExit("Set the local LIVE_LOGIN_EMAIL and LIVE_LOGIN_PASSWORD values first.")

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chromium")
    page = browser.new_page(viewport={"width": 390, "height": 844})
    page.goto(base + "/login/")
    expect(page.get_by_label("Email address")).to_be_visible()
    page.locator("#id_username").fill(email)
    page.locator("#id_password").fill(password)
    page.get_by_role("button", name="Sign in").click()
    page.wait_for_url("**/business/new/", timeout=60000)
    expect(page.get_by_role("heading", name="Tell us about your business.")).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
    browser.close()
print("Live owner sign-in succeeded and opened the business setup screen. No financial records were created.")
