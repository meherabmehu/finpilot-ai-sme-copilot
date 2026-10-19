"""Real local browser workflow; synthetic workspaces only, no production network."""
# ruff: noqa: E402
import json
import os
from pathlib import Path
import threading
from uuid import uuid4
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor
from wsgiref.simple_server import make_server, WSGIRequestHandler

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.conf import settings
from django.utils import timezone
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.wsgi import get_wsgi_application
from apps.portal.models import Business
from playwright.sync_api import sync_playwright, expect

if not settings.DEBUG or settings.HOSTED:
    raise RuntimeError('Only local synthetic tests are authorized.')
retail = Business.objects.get(name='Competition Synthetic Retail', is_demo=True)
restaurant = Business.objects.get(name='Competition Synthetic Restaurant', is_demo=True)
before = list(retail.transactions.order_by('pk').values('pk', 'amount', 'date', 'status', 'due_date'))
output = Path('test-results/competition-browser')
output.mkdir(parents=True, exist_ok=True)


class Quiet(WSGIRequestHandler):
    def log_message(self, *args):
        pass


server = make_server('127.0.0.1', 0, StaticFilesHandler(get_wsgi_application()), handler_class=Quiet)
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f'http://127.0.0.1:{server.server_port}'
checks, errors, audits = [], [], []


def database_call(function):
    # Playwright's sync bridge owns an event loop in this thread.
    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(function).result()
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chromium')
        page = browser.new_page(viewport={'width': 1440, 'height': 1000})
        page.emulate_media(reduced_motion='reduce')
        page.on('pageerror', lambda error: errors.append(str(error)))
        if Path('test-results/axe.min.js').exists():
            page.context.add_init_script(path='test-results/axe.min.js')
        page.goto(base+'/login/')
        page.locator('#id_username').fill('competition@finpilot.local')
        page.locator('#id_password').fill(os.environ['DEMO_PASSWORD'])
        page.get_by_role('button', name='Sign in', exact=True).click()
        page.wait_for_url('**/b/*/')
        # Actual onboarding and data-entry/import workflow in a new local synthetic workspace.
        page.goto(base+'/business/new/')
        page.locator('#id_name').fill('Competition E2E Synthetic '+uuid4().hex[:8])
        page.locator('#id_category').select_option('Retail')
        page.locator('#id_country').select_option('US')
        page.locator('#id_currency').select_option('USD')
        page.locator('#id_opening_balance').fill('5000')
        page.locator('#id_opening_date').fill((timezone.localdate()-timedelta(days=30)).isoformat())
        page.locator('#id_low_cash_threshold').fill('1000')
        page.locator('#id_cash_records_complete').check()
        page.locator('form button[type=submit], form button.button.primary').last.click()
        page.wait_for_url('**/b/*/')
        new_prefix = page.url.removeprefix(base)
        database_call(lambda: Business.objects.filter(pk=new_prefix.split('/')[2]).update(is_demo=True))
        page.goto(base+new_prefix+'transaction/new/')
        page.locator('#id_description').fill('SYNTHETIC browser sale')
        page.locator('#id_amount').fill('100')
        page.locator('#id_kind').select_option('income')
        page.locator('#id_category').fill('Sales')
        page.get_by_role('button', name='Save transaction').click()
        expect(page.get_by_role('status')).to_contain_text('Transaction saved')
        page.goto(base+new_prefix+'business/?tab=upload')
        payload = ('date,description,amount,kind,currency,status,category,reference,due_date\n'
                   f'{timezone.localdate()},SYNTHETIC imported invoice,200,receivable,USD,pending,Sales,SYN-BROWSER-INVOICE,{timezone.localdate()-timedelta(days=2)}\n')
        page.locator('input[type=file]').set_input_files({'name': 'synthetic.csv', 'mimeType': 'text/csv', 'buffer': payload.encode()})
        page.get_by_role('button', name='Preview import').click()
        expect(page.get_by_role('heading', name='Review your import')).to_be_visible()
        page.get_by_role('button', name='Confirm 1 rows').click()
        expect(page.get_by_role('status')).to_contain_text('1 transactions imported')
        page.goto(base+new_prefix)
        expect(page.get_by_role('heading', name='Current cash', exact=True).locator('..')).to_contain_text('5,100.00')
        # Question refusal must not generate a financial report.
        page.goto(base+new_prefix+'advisor/')
        page.locator('textarea[name=question], input[name=question]').first.fill('Who won the FIFA World Cup in 2022?')
        page.get_by_role('button', name='Send question', exact=True).click()
        expect(page.locator('.chat-messages')).to_contain_text('outside FinPilot')
        prefix = f'/b/{retail.pk}/'
        page.goto(base+prefix+'planning/?tab=scenarios')
        page.locator('#id_recovery-0-include').check()
        page.get_by_role('button', name='Test recovery & find combinations').click()
        expect(page.get_by_role('heading', name='Explicit invoice recovery result')).to_be_visible()
        expect(page.get_by_text('Bounded combined alternatives', exact=True)).to_be_visible()
        page.get_by_role('button', name='Calculate & save recovery', exact=True).click()
        expect(page.get_by_role('status')).to_contain_text('Hypothetical invoice scenario saved')
        page.get_by_role('button', name='Transfer assumptions to Decision Lab', exact=True).click()
        page.wait_for_url('**/investigations/*/')
        detail = page.url
        page.goto(detail+'?step=5')
        page.get_by_role('button', name='Accept this plan', exact=True).click()
        expect(page.get_by_role('heading', name='Decision memory \u00b7 Accepted')).to_be_visible()
        page.goto(base+prefix+'planning/?tab=roadmap')
        expect(page.get_by_text('Confirm funding and agreements before payment deadline', exact=True)).to_be_visible()
        task = page.locator('.roadmap-item').first
        task.get_by_text('Update owner-reported progress', exact=True).click()
        task.locator('select[name$="-status"]').select_option('in_progress')
        task.get_by_role('button', name='Save task progress').click()
        expect(page.locator('.roadmap-item').first).to_contain_text('In progress')
        assert database_call(lambda: list(retail.transactions.order_by('pk').values('pk', 'amount', 'date', 'status', 'due_date'))) == before
        for width in (320, 390, 768, 1440):
            page.set_viewport_size({'width': width, 'height': 1000})
            for label, path in [('retail', prefix), ('records', prefix+'business/?tab=transactions'),
                                ('recovery', prefix+'planning/?tab=scenarios'), ('forecast', prefix+'planning/?tab=forecast'),
                                ('loans', prefix+'planning/?tab=loans'), ('roadmap', prefix+'planning/?tab=roadmap'),
                                ('reports', prefix+'reports/'), ('restaurant', f'/b/{restaurant.pk}/')]:
                response = page.goto(base+path)
                assert response.status == 200
                if not page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'):
                    offenders = page.evaluate("[...document.querySelectorAll('main *')].filter(e=>e.getBoundingClientRect().right>innerWidth+1).slice(0,8).map(e=>({tag:e.tagName,cls:e.className,width:e.getBoundingClientRect().width,text:e.textContent.slice(0,80)}))")
                    raise AssertionError((label, width, offenders))
                checks.append({'page': label, 'width': width})
                if width in (390, 1440):
                    page.screenshot(path=str(output/f'{label}-{width}.png'), full_page=True)
                    if Path('test-results/axe.min.js').exists():
                        violations = page.evaluate("async () => (await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}})).violations.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)}))")
                        audits.append({'page': label, 'width': width, 'violations': violations})
        page.goto(base+prefix+'planning/?tab=loans')
        page.get_by_text('Custom calculator: enter actual quoted lender terms', exact=True).click()
        page.locator('#id_amount').fill('10000')
        page.locator('#id_annual_rate').fill('12')
        page.locator('#id_months').fill('12')
        page.locator('#id_fees').fill('200')
        page.locator('#id_monthly_capacity').fill('1000')
        page.get_by_role('button', name='Compare financing').click()
        expect(page.locator('.loan-number')).to_contain_text('888.49')
        expect(page.locator('main')).to_contain_text('10861.86')
        for fmt in ('csv', 'xlsx', 'pdf'):
            response = page.request.get(base+prefix+f'reports/?type=roadmap&format={fmt}')
            assert response.status == 200 and len(response.body()) > 100
        page.goto(base+f'/b/{restaurant.pk}/advisor/')
        page.locator('textarea[name=question], input[name=question]').first.fill('How can my restaurant survive a 20% sales reduction?')
        page.get_by_role('button', name='Send question', exact=True).click()
        expect(page.locator('.chat-messages')).to_contain_text('20% revenue decline')
        expect(page.locator('.chat-messages')).to_contain_text('food replenishment')
        # A separate explicit synthetic paid entry updates current state and marks old evidence stale.
        page.goto(base+prefix+'transaction/new/')
        page.locator('#id_description').fill('SYNTHETIC explicit post-decision receipt')
        page.locator('#id_amount').fill('50')
        page.locator('#id_kind').select_option('income')
        page.get_by_role('button', name='Save transaction').click()
        page.goto(detail+'?step=1')
        expect(page.get_by_label('Historical versus current financial evidence')).to_contain_text('Needs Review')
        page.keyboard.press('Tab')
        assert page.evaluate('document.activeElement !== document.body')
        browser.close()
    report = {'checks': checks, 'accessibility': audits, 'page_errors': errors,
              'synthetic_onboarding_import': True, 'recovery_acceptance_task_progress': True,
              'decision_did_not_change_ledger': True, 'explicit_synthetic_receipt_caused_staleness': True}
    (output/'verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'viewport_checks': len(checks), 'accessibility_audits': len(audits), 'page_errors': errors,
                      'accessibility_failures': [a for a in audits if a['violations']]}))
    assert not errors and not any(a['violations'] for a in audits)
finally:
    server.shutdown()
    server.server_close()
