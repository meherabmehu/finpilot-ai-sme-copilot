"""Finite local browser check. Run as python -m scripts.browser_decisions after seeding."""
# ruff: noqa: E402
import json
import os
import threading
from pathlib import Path
from wsgiref.simple_server import make_server, WSGIRequestHandler

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django

django.setup()
from django.conf import settings
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.wsgi import get_wsgi_application
from apps.portal.models import Business
from playwright.sync_api import sync_playwright

if not settings.DEBUG:
    raise RuntimeError('Local synthetic browser workflow requires DEBUG.')
password = os.environ['DEMO_PASSWORD']
business = Business.objects.get(name='Decision Lab · Synthetic Liquidity Demo', is_demo=True)


class QuietHandler(WSGIRequestHandler):
    def log_message(self, *args):
        pass


server = make_server('127.0.0.1', 0, StaticFilesHandler(get_wsgi_application()), handler_class=QuietHandler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
base = f'http://127.0.0.1:{server.server_port}'
prefix = f'/b/{business.pk}/'
results = []
try:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1440, 'height': 1000})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(base+'/login/')
        page.locator('#id_username').fill('decisions@finpilot.local')
        page.locator('#id_password').fill(password)
        page.get_by_role('button', name='Sign in', exact=True).click()
        page.wait_for_url('**/b/*/')
        assert page.get_by_role('heading', name='Financial Watchtower').is_visible()
        page.goto(base+prefix+'planning/?tab=decisions')
        page.locator('#id_question').fill('Can I pay my supplier and protect payroll?')
        page.get_by_role('button', name='Investigate & compare alternatives').click()
        page.wait_for_url('**/investigations/*/')
        detail = page.url
        assert page.get_by_role('heading', name='Compare simulated alternatives').is_visible()
        page.get_by_role('button', name='Record this plan').first.click()
        assert page.get_by_role('heading', name='Decision memory · Accepted').is_visible()
        page.get_by_role('button', name='Check monitoring & outcome').click()
        assert page.get_by_role('heading', name='Decision memory · Monitoring').is_visible()
        paths = [base+prefix, base+prefix+'business/', base+prefix+'advisor/',
                 base+prefix+'planning/?tab=decisions', base+prefix+'reports/?type=investigations', detail]
        for width in [320, 375, 390, 768, 1024, 1440, 1920]:
            page.set_viewport_size({'width': width, 'height': 1000})
            for url in paths:
                response = page.goto(url)
                assert response.status == 200, (url, response.status)
                if url == detail:
                    page.locator('details').evaluate_all('(nodes) => nodes.forEach(node => { node.open = true; })')
                overflow = page.evaluate('document.documentElement.scrollWidth > window.innerWidth + 1')
                results.append({'width': width, 'path': url.replace(base, ''), 'horizontal_overflow': overflow})
        assert not errors, errors
        output = Path('test-results')
        output.mkdir(exist_ok=True)
        (output/'decision-responsive.json').write_text(json.dumps({'checks': results, 'page_errors': errors}, indent=2))
        print(json.dumps({'pages_checked': len(results), 'overflow_count': sum(r['horizontal_overflow'] for r in results), 'page_errors': errors}))
        browser.close()
finally:
    server.shutdown()
