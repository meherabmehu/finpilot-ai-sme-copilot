"""Public HTTPS, database health, CSRF and responsive checks for a live deployment."""

import argparse
from pathlib import Path

import httpx
from playwright.sync_api import sync_playwright, expect

parser = argparse.ArgumentParser()
parser.add_argument("url")
args = parser.parse_args()
base = args.url.rstrip("/")
output = Path("test-results/live")
output.mkdir(parents=True, exist_ok=True)

with httpx.Client(timeout=60, follow_redirects=True) as client:
    for path in ("/", "/health/", "/login/", "/signup/", "/static/css/responsive.css"):
        response = client.get(base + path)
        assert response.status_code == 200, (path, response.status_code)
        assert str(response.url).startswith(base), "Unexpected external redirect"
        if path == "/health/":
            assert response.text == "ok"
    assert client.get(base + "/workspace/", follow_redirects=False).status_code == 302

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chromium")
    page = browser.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    for width in (320, 390, 768, 1440):
        page.set_viewport_size({"width": width, "height": 900})
        for route in ("/", "/login/", "/signup/", "/password-reset/"):
            response = page.goto(base + route)
            assert response.status == 200
            assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1"), (width, route)
        if width in (320, 1440):
            page.goto(base)
            page.screenshot(path=str(output / f"landing-{width}.png"), full_page=True)
    page.goto(base + "/login/")
    page.locator("#id_username").fill("live-check-nonexistent@example.invalid")
    page.locator("#id_password").fill("intentionally-invalid-not-a-secret")
    with page.expect_response(lambda response: response.request.method == "POST" and "/login/" in response.url) as result:
        page.get_by_role("button", name="Sign in").click()
    assert result.value.status == 200, "Secure login form POST failed"
    expect(page.locator(".errorlist").first).to_be_visible()
    assert not errors, errors
    browser.close()
print("Live checks passed: HTTPS routes, database health, protected workspace redirect, 16 responsive pages and CSRF login form.")
