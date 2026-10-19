"""Synthetic local browser checks with mocked Groq; real inference is checked separately."""
# ruff: noqa: E402
import json
import os
from pathlib import Path
import threading
from unittest.mock import patch
from wsgiref.simple_server import make_server, WSGIRequestHandler

os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
import httpx
from django.conf import settings
from django.test import override_settings
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.wsgi import get_wsgi_application
from apps.portal.models import Business
from playwright.sync_api import sync_playwright, expect

QUESTIONS = ['How much overdue money do I have?', 'Why is my reserve at risk on October 25?',
    'Which supplier payment should I prioritize?', 'Can I protect my reserve without borrowing?',
    'What if the customer pays only half?', 'Why did my restaurant operating expenses increase?',
    'What if sales decline by 20%?', 'Is this loan safe for my business?',
    'What should I do before my supplier deadline?', 'Who won the FIFA World Cup in 2022?',
    'আমার বকেয়া পাওনা কত?', 'কাস্টমার অর্ধেক টাকা দিলে?', 'বিক্রি ২০% কমে গেলে?',
    'bokeya paona koto?', 'loan chara reserve protect korbo kivabe?', 'restaurant khoroch keno bereche?']


class Quiet(WSGIRequestHandler):
    def log_message(self,*args):
        pass


def mock_response(*args,**kwargs):
    scope=kwargs['json']['response_format']['json_schema']['name']=='financial_scope'
    data={'scope':'financial'} if scope else {'evidence_ids':['F1'],'action_ids':['review'],'question_ids':[],
        'reasoning':[{'premise_ids':['F1'],'relationship':'operations_dependency',
        'hypothesis':'If the owner confirms the operating dependency, reviewing the payment terms could clarify the practical tradeoff.', 'action_id':'review'}]}
    return httpx.Response(200,json={'choices':[{'message':{'content':json.dumps(data)}}]},request=httpx.Request('POST','https://api.groq.com/openai/v1/chat/completions'))


def main():
    if not settings.DEBUG or settings.HOSTED:
        raise RuntimeError('Only an existing local synthetic business is permitted.')
    business=Business.objects.get(name='Competition Synthetic Retail',is_demo=True)
    before=list(business.transactions.order_by('pk').values('pk','status','amount','date','due_date'))
    output=Path('test-results/final-advisor-browser')
    output.mkdir(parents=True,exist_ok=True)
    server=make_server('127.0.0.1',0,StaticFilesHandler(get_wsgi_application()),handler_class=Quiet)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    base=f'http://127.0.0.1:{server.server_port}'
    errors=[]
    audits=[]
    try:
        with override_settings(FINPILOT_AI_ENABLED=True,FINPILOT_AI_PROVIDER='groq',GROQ_API_KEY='synthetic-browser-key'), patch('apps.portal.intelligence.ai_grounding.httpx.Client.post',side_effect=mock_response):
            with sync_playwright() as pw:
                browser=pw.chromium.launch(channel='chromium')
                page=browser.new_page(viewport={'width':1440,'height':1000})
                page.on('pageerror',lambda error:errors.append(str(error)))
                page.context.add_init_script(path='test-results/axe.min.js')
                page.goto(base+'/login/')
                page.locator('#id_username').fill('competition@finpilot.local')
                page.locator('#id_password').fill(os.environ['DEMO_PASSWORD'])
                page.get_by_role('button',name='Sign in',exact=True).click()
                page.wait_for_url('**/b/*/')
                page.goto(base+f'/b/{business.pk}/advisor/')
                for question in QUESTIONS:
                    page.locator('#question').fill(question)
                    page.get_by_role('button',name='Send question',exact=True).click()
                    response=page.locator('article.chat-message.assistant').last
                    expect(response).to_contain_text('outside FinPilot' if 'FIFA' in question else 'Groq-assisted')
                    expect(page.locator('.page-heading .pill')).not_to_contain_text('not configured')
                for width in (320,390,768,1440):
                    page.set_viewport_size({'width':width,'height':1000})
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
                    if width in (390,1440):
                        page.screenshot(path=str(output/f'advisor-{width}.png'),full_page=True)
                        violations=page.evaluate("async () => (await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}})).violations.map(v=>v.id)")
                        audits.append({'width':width,'violations':violations})
                browser.close()
        after=list(business.transactions.order_by('pk').values('pk','status','amount','date','due_date'))
        assert after==before and not errors and not any(a['violations'] for a in audits)
        report={'questions':len(QUESTIONS),'viewport_checks':4,'accessibility':audits,'page_errors':errors,
                'groq_transport':'mocked; real synthetic API check is separate','groq_badge_verified':True,'financial_records_unchanged':True}
        (output/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps(report))
    finally:
        server.shutdown()
        server.server_close()


if __name__=='__main__':
    main()
