"""Verify public and authenticated layouts across viewport widths and orientations."""

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
parser = argparse.ArgumentParser()
parser.add_argument("--widths", default="320,360,390,430,600,768,960,1024,1280,1440,1920,2560")
args = parser.parse_args()
base = os.getenv("BROWSER_BASE_URL", "http://127.0.0.1:8000")
output = ROOT / "test-results" / "responsive"
output.mkdir(parents=True, exist_ok=True)
sizes = [(int(width), 900) for width in args.widths.split(",")] + [(568, 320), (844, 390)]
failures, errors = [], []
checks = 0

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chromium")
    context = browser.new_context()
    page = context.new_page()
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(base + "/login/")
    page.locator("#id_username").fill("demo@finpilot.local")
    page.locator("#id_password").fill(os.environ["DEMO_PASSWORD"])
    page.get_by_role("button", name="Sign in").click()
    page.wait_for_url("**/b/*/")
    workspace = page.url.rstrip("/")
    routes = ["/", "/login/", "/signup/", "/password-reset/", "/info/privacy/", "/business/new/"]
    routes += [
        workspace.removeprefix(base) + suffix
        for suffix in [
            "/",
            "/business/",
            "/business/?tab=transactions",
            "/business/?tab=sales",
            "/business/?tab=expenses",
            "/business/?tab=upload",
            "/transaction/new/",
            "/advisor/",
            "/planning/",
            "/planning/?tab=scenarios",
            "/planning/?tab=loans",
            "/reports/",
        ]
    ]

    def measure(label):
        global checks
        checks += 1
        overflow = page.evaluate("""() => {
            const width = document.documentElement.clientWidth;
            if (document.documentElement.scrollWidth <= width + 1) return [];
            const elements = [...document.querySelectorAll('body *')].filter(el => {
                const box = el.getBoundingClientRect();
                return box.width && (box.right > width + 1 || box.left < -1) &&
                    !el.closest('.table-scroll, .tabs, .chat-messages') &&
                    getComputedStyle(el).position !== 'absolute';
            }).slice(0, 8).map(el => ({tag: el.tagName, class: el.className,
                right: Math.round(el.getBoundingClientRect().right)}));
            return elements.length ? elements : [{documentWidth: document.documentElement.scrollWidth, viewportWidth: width}];
        }""")
        if overflow:
            failures.append({"viewport": size, "route": label, "overflow": overflow})

    for size in sizes:
        page.set_viewport_size({"width": size[0], "height": size[1]})
        for route in routes:
            response = page.goto(base + route)
            if response.status != 200:
                failures.append({"viewport": size, "route": route, "status": response.status})
                continue
            measure(route)
            if route == workspace.removeprefix(base) + "/":
                for selector in [".switcher", ".notifications", ".profile"]:
                    page.locator(selector + " summary").click()
                    menu = page.locator(selector + " .dropdown")
                    box = menu.bounding_box()
                    checks += 1
                    if not box or box["x"] < -1 or box["x"] + box["width"] > size[0] + 1 or box["y"] + box["height"] > size[1] + 1:
                        failures.append({"viewport": size, "menu": selector, "bounds": box})
                    page.locator(selector + " summary").click()
                if size[0] in (320, 768, 1440):
                    page.screenshot(path=str(output / f"dashboard-{size[0]}x{size[1]}.png"), full_page=True)
        # Stress text and values without changing any saved business data.
        page.goto(workspace + "/")
        page.locator(".switcher strong").evaluate("el => el.textContent = 'International Business With A Very Long Workspace Name'")
        page.locator(".stat-card h2").first.evaluate("el => el.textContent = 'USD 999,999,999,999.99'")
        measure("long names and monetary values")
    browser.close()

report = {"checks": checks, "viewports": sizes, "failures": failures, "javascript_errors": errors}
(output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
raise SystemExit(bool(failures or errors))
