"""Local marked synthetic B2C workflow and seven-width browser evidence."""
# ruff: noqa: E402
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from uuid import uuid4
from wsgiref.simple_server import make_server,WSGIRequestHandler
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from django.conf import settings
from django.utils import timezone
from django.core.wsgi import get_wsgi_application
from django.contrib.staticfiles.handlers import StaticFilesHandler
from apps.portal.models import Business
from apps.portal.intelligence.personal_finance import personal_state
from playwright.sync_api import sync_playwright,expect


class Quiet(WSGIRequestHandler):
    def log_message(self,*args):
        pass


def database(function):
    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(function).result()


def main():
    assert settings.DEBUG and not settings.HOSTED
    output=Path('test-results/buildathon-browser')
    output.mkdir(parents=True,exist_ok=True)
    screenshots=Path('static/submission/images')
    screenshots.mkdir(parents=True,exist_ok=True)
    server=make_server('127.0.0.1',0,StaticFilesHandler(get_wsgi_application()),handler_class=Quiet)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    base=f'http://127.0.0.1:{server.server_port}'
    checks=[]
    audits=[]
    errors=[]
    exports=[]
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(channel='chromium')
            page=browser.new_page(viewport={'width':1440,'height':1000})
            page.emulate_media(reduced_motion='reduce')
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.context.add_init_script(path='test-results/axe.min.js')
            page.goto(base+'/demo/personal/')
            page.locator('#id_scenario').select_option('delay')
            page.locator('#id_delay_days').select_option('7')
            page.locator('#id_income_reference').select_option('demo-income')
            page.get_by_role('button',name='Compare synthetic scenario',exact=True).click()
            expect(page.locator('#personal-result')).to_contain_text('2000.00')
            assert page.request.get(base+'/demo/personal/?format=pdf').body().startswith(b'%PDF')
            page.goto(base+'/login/')
            page.locator('#id_username').fill('personal-demo@finpilot.local')
            page.locator('#id_password').fill(os.environ['DEMO_PASSWORD'])
            page.get_by_role('button',name='Sign in',exact=True).click()
            page.wait_for_url('**/b/*/')
            page.goto(base+'/personal/new/')
            page.locator('#id_name').fill('SYNTHETIC Consumer '+uuid4().hex[:6])
            page.locator('#id_income_type').select_option('freelance')
            for key,value in [('available_cash','18000'),('reserve','8000'),('savings_target','5000'),('expected_income','10000'),('monthly_essentials','12000')]:
                page.locator('#id_'+key).fill(value)
            page.locator('#id_income_date').fill(str(timezone.localdate()+timedelta(days=4)))
            page.locator('#id_bills_date').fill(str(timezone.localdate()+timedelta(days=7)))
            page.locator('#id_complete').check()
            page.get_by_role('button',name='Create personal workspace',exact=True).click()
            page.wait_for_url('**/b/*/')
            prefix=page.url.removeprefix(base)
            workspace_id=prefix.split('/')[2]
            database(lambda:Business.objects.filter(pk=workspace_id).update(is_demo=True))
            page.reload()
            expect(page.get_by_role('heading',name='Your money, with a clearer plan.')).to_be_visible()
            page.screenshot(path=str(screenshots/'personal-dashboard.png'),full_page=False)
            before=database(lambda:personal_state(Business.objects.get(pk=workspace_id))['fingerprint'])
            page.goto(base+prefix+'planning/')
            page.locator('#id_scenario').select_option('delay')
            page.locator('#id_delay_days').select_option('7')
            page.locator('#id_income_reference').select_option(index=1)
            page.locator('#id_save').check()
            page.get_by_role('button',name='Compare with baseline',exact=True).click()
            expect(page.locator('#personal-result')).to_contain_text('2000.00')
            page.locator('#personal-result').screenshot(path=str(screenshots/'personal-scenario.png'))
            assert database(lambda:personal_state(Business.objects.get(pk=workspace_id))['fingerprint'])==before
            for width in (320,375,390,768,1024,1440,1920):
                page.set_viewport_size({'width':width,'height':1000})
                for name,path in [('landing','/'),('demo','/demo/personal/'),('onboarding','/personal/new/'),('dashboard',prefix),
                    ('records',prefix+'business/'),('advisor',prefix+'advisor/'),('planning',prefix+'planning/'),('reports',prefix+'reports/')]:
                    response=page.goto(base+path)
                    assert response.status==200,(name,response.status)
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(name,width)
                    checks.append({'page':name,'width':width})
                    if width in (390,1440):
                        page.screenshot(path=str(output/f'{name}-{width}.png'),full_page=True)
                        violations=page.evaluate("async () => (await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}})).violations.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)}))")
                        audits.append({'page':name,'width':width,'violations':violations})
            page.set_viewport_size({'width':1440,'height':1000})
            page.goto(base+prefix+'advisor/')
            page.locator('#question').fill('Can I afford to spend 5,000 BDT this week?')
            page.get_by_role('button',name='Send question',exact=True).click()
            expect(page.locator('.chat-messages')).to_contain_text('5000.00')
            page.screenshot(path=str(output/'personal-advisor-offline.png'),full_page=False)
            for fmt in ('pdf','csv','xlsx'):
                response=page.request.get(base+prefix+'reports/?format='+fmt)
                assert response.status==200 and len(response.body())>100
                exports.append(fmt)
            page.goto(base+prefix+'transaction/new/')
            page.locator('#id_description').fill('SYNTHETIC actual personal receipt')
            page.locator('#id_amount').fill('1000')
            page.locator('#id_kind').select_option('income')
            page.locator('#id_category').select_option('Salary')
            page.get_by_role('button',name='Save transaction',exact=False).click()
            assert database(lambda:personal_state(Business.objects.get(pk=workspace_id))['known_cash'])=='19000.00'
            browser.close()
        report={'viewport_checks':len(checks),'accessibility':audits,'page_errors':errors,'exports':exports,
            'onboarding_and_actual_income':True,'saved_scenario_did_not_change_ledger':True,
            'sticker_asset_present':any((Path('static/buildathon')/('yunet-aignite-buildathon-2026-sticker.'+ext)).exists() for ext in ('png','jpg','jpeg','webp'))}
        (output/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps(report))
        assert not errors and not any(a['violations'] for a in audits)
    finally:
        server.shutdown()
        server.server_close()


if __name__=='__main__':
    main()
