"""Local synthetic visual, interaction and accessibility checks; no production URLs."""
# ruff: noqa: E402
import json
import os
from pathlib import Path
import threading
from wsgiref.simple_server import make_server, WSGIRequestHandler

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.conf import settings
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.wsgi import get_wsgi_application
from django.urls import reverse
from apps.portal.models import Business
from playwright.sync_api import sync_playwright, expect

if not settings.DEBUG:
    raise RuntimeError('Only a local DEBUG synthetic workspace may be inspected.')
business = Business.objects.get(name='Decision Lab \u00b7 Synthetic Liquidity Demo', is_demo=True)
before = list(business.transactions.order_by('pk').values('id', 'date', 'amount', 'status', 'due_date'))
output = Path('test-results/survival')
output.mkdir(parents=True, exist_ok=True)


class QuietHandler(WSGIRequestHandler):
    def log_message(self, *args):
        pass


server = make_server('127.0.0.1', 0, StaticFilesHandler(get_wsgi_application()), handler_class=QuietHandler)
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f'http://127.0.0.1:{server.server_port}'
prefix = f'/b/{business.pk}/'
results = []
errors = []
accessibility = []
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chromium')
        page = browser.new_page(viewport={'width': 1440, 'height': 1000})
        page.emulate_media(reduced_motion='reduce')
        axe = Path('test-results/axe.min.js')
        if axe.is_file():
            # DevTools preload keeps the application's strict CSP unchanged.
            page.context.add_init_script(path=str(axe))
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(base + '/login/')
        page.locator('#id_username').fill('decisions@finpilot.local')
        page.locator('#id_password').fill(os.environ['DEMO_PASSWORD'])
        page.get_by_role('button', name='Sign in', exact=True).click()
        page.wait_for_url('**/b/*/')
        expect(page.locator('#primary-risk')).to_be_visible()
        page.goto(base + prefix + 'planning/')
        page.locator('#id_question').fill('Can I protect payroll without taking a loan?')
        page.get_by_role('button', name='Explore options', exact=True).click()
        page.wait_for_url('**/investigations/*/')
        detail = page.url
        expect(page.get_by_role('heading', name='Understand the problem')).to_be_visible()
        page.get_by_role('link', name='Next: Explore options').click()
        page.get_by_role('link', name='Test this option').first.click()
        expect(page.get_by_role('heading', name='Test collection uncertainty')).to_be_visible()
        page.locator('#delay').fill('14')
        page.get_by_role('button', name='Recalculate assumptions').click()
        expect(page.get_by_role('heading', name='No customer collections')).to_be_visible()
        page.get_by_role('link', name='Next: Compare plans').click()
        expect(page.get_by_role('heading', name='Compare simulated alternatives')).to_be_visible()
        page.get_by_role('link', name='Next: Recovery plan').click()
        if page.get_by_role('button', name='Accept this plan', exact=True).count():
            page.get_by_role('button', name='Accept this plan', exact=True).click()
            expect(page.get_by_role('heading', name='Decision memory \u00b7 Accepted')).to_be_visible()
            page.get_by_role('button', name='Check monitoring & outcome').click()
            expect(page.get_by_role('heading', name='Decision memory \u00b7 Monitoring')).to_be_visible()

        paths = [('dashboard', prefix), ('business', prefix+'business/'), ('advisor', prefix+'advisor/'),
                 ('lab', prefix+'planning/'), ('reports', prefix+'reports/'),
                 ('rules', prefix+'business/?tab=rules'), ('data', prefix+'business/?tab=transactions'),
                 ('upload', prefix+'business/?tab=upload'), ('forecast', prefix+'planning/?tab=forecast'),
                 ('scenarios', prefix+'planning/?tab=scenarios'), ('loans', prefix+'planning/?tab=loans')]
        paths += [(f'step-{step}', detail.removeprefix(base) + f'?step={step}') for step in range(1, 6)]
        for width in (360, 390, 768, 1024, 1366, 1440, 1920):
            page.set_viewport_size({'width': width, 'height': 1000 if width > 700 else 844})
            for label, path in paths:
                response = page.goto(base + path)
                assert response.status == 200, (path, response.status)
                expect(page.locator('h1')).to_have_count(1)
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), (label, width, 'overflow')
                active = page.locator('nav[aria-label="Main navigation"] a.active')
                expect(active).to_have_count(1)
                if label in ('dashboard', 'business', 'advisor', 'lab', 'reports') and width in (390, 1440):
                    page.evaluate('document.fonts.ready')
                    page.screenshot(path=str(output/f'{label}-{width}.png'), full_page=True)
                    if axe.is_file():
                        audit = page.evaluate("""async () => {
                          const result = await axe.run(document, {runOnly: {type:'tag', values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}});
                          return {violations:result.violations.map(v => ({id:v.id,impact:v.impact,help:v.help,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))})), incomplete:result.incomplete.length};
                        }""")
                        accessibility.append({'page': label, 'width': width, **audit})
                if label.startswith('step-'):
                    expect(page.locator('[aria-current="step"]')).to_have_count(1)
                # Browser-computed baseline legibility, rather than a CSS-source claim.
                size = page.locator('h1').evaluate('(node) => parseFloat(getComputedStyle(node).fontSize)')
                assert size >= 24, (label, width, size)
                results.append({'page': label, 'width': width, 'overflow': False, 'h1_px': size})

        # All advertised primary report buttons produce actual attachments.
        page.goto(base + prefix+'reports/')
        for kind in ('summary', 'forecast', 'decisions', 'receivables', 'payables'):
            for fmt in ('csv', 'xlsx', 'pdf'):
                response = page.request.get(base + reverse('reports', args=[business.pk]) + f'?type={kind}&format={fmt}')
                assert response.status == 200 and 'attachment' in response.headers.get('content-disposition', ''), (kind, fmt)
                assert len(response.body()) > 100
        # Keyboard focus and reduced-motion preference smoke checks.
        page.goto(base + prefix)
        page.keyboard.press('Tab')
        assert page.evaluate('document.activeElement !== document.body')
        page.emulate_media(reduced_motion='reduce')
        assert page.evaluate('matchMedia("(prefers-reduced-motion: reduce)").matches')
        assert not errors, errors
        browser.close()
    after = list(business.transactions.order_by('pk').values('id', 'date', 'amount', 'status', 'due_date'))
    assert after == before, 'A decision flow changed actual financial records.'
    report = {'viewport_checks': len(results), 'export_checks': 15, 'page_errors': errors,
              'keyboard_focus': True, 'reduced_motion': True, 'actual_financial_records_unchanged': True,
              'axe_audits': accessibility, 'checks': results}
    (output/'verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({key: value for key, value in report.items() if key not in ('checks', 'axe_audits')}))
    print(json.dumps({'axe_pages': len(accessibility), 'violations': [a for a in accessibility if a['violations']]}))
    assert not any(a['violations'] for a in accessibility), 'Resolve automated WCAG findings before delivery.'
finally:
    server.shutdown()
    server.server_close()
