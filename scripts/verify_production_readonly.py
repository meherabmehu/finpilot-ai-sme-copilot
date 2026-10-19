"""Approved hosts only; no ledger/chat writes, credentials or financial output."""
import argparse
import json
from pathlib import Path
import re
from urllib.parse import urljoin, urlsplit

import httpx
from dotenv import dotenv_values


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origin',required=True,choices=['https://finpilot-ai-web.onrender.com','https://finpilot-ai-sme-copilot.vercel.app'])
    args=parser.parse_args()
    base=args.origin
    values=dotenv_values('.env')
    report={'origin':base,'checks':[],'ledger_modified':False,'chat_modified':False}

    def target(location):
        full=urljoin(base,location)
        if urlsplit(full).netloc!=urlsplit(base).netloc or urlsplit(full).scheme!='https':
            raise ValueError('Cross-origin redirect refused.')
        return full

    def record(name,response):
        response.raise_for_status()
        report['checks'].append({'name':name,'status':response.status_code})

    with httpx.Client(timeout=40,follow_redirects=False) as client:
        record('Landing',client.get(base+'/'))
        record('Database health',client.get(base+'/health/'))
        login=client.get(base+'/login/')
        record('Login',login)
        for path in re.findall(r'href="([^"]*/css/(?:survival|polish)[^"]*\.css)"',login.text):
            record('Static stylesheet',client.get(target(path)))
        assert values.get('LIVE_LOGIN_EMAIL') and values.get('LIVE_LOGIN_PASSWORD'), 'Existing verification credentials unavailable.'
        token=re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"',login.text)
        response=client.post(base+'/login/',data={'username':values['LIVE_LOGIN_EMAIL'],'password':values['LIVE_LOGIN_PASSWORD'],
            'csrfmiddlewaretoken':token.group(1)},headers={'Referer':base+'/login/','Origin':base})
        assert response.status_code in (302,303),'Existing account authentication failed.'
        for _ in range(6):
            if response.status_code not in (301,302,303,307,308):
                break
            response=client.get(target(response.headers['location']))
        record('Authenticated workspace',response)
        match=re.search(r'/b/[0-9a-f-]+/',str(response.url))
        assert match,'No authorized existing business selected; no test business was created.'
        prefix=match.group()
        for name,suffix in [('Dashboard',''),('My Business','business/'),('Financial rules','business/?tab=rules'),
            ('AI Advisor','advisor/'),('Financial Planning','planning/'),('Reports','reports/'),
            ('Recurring','business/?tab=recurring'),('Decision Lab','planning/?tab=decisions'),
            ('Forecast','planning/?tab=forecast'),('Scenarios','planning/?tab=scenarios'),
            ('Loans','planning/?tab=loans'),('Roadmap','planning/?tab=roadmap')]:
            response=client.get(base+prefix+suffix)
            record(name,response)
            if name=='AI Advisor':
                badge=re.search(r'<span class="pill neutral">(.*?)</span>',response.text,re.S)
                report['configured_provider_badge']=bool(badge and 'configured' in badge.group(1) and 'not configured' not in badge.group(1))
                assert report['configured_provider_badge'],'Configured Groq was not recognized by the Advisor badge.'
        report['authenticated_pages']=12
    destination=Path('test-results/final-production-'+('render' if 'onrender.com' in base else 'vercel')+'.json')
    destination.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))


if __name__=='__main__':
    main()
