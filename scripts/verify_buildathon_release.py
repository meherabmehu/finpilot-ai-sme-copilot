"""Verify public synthetic workflow and submission files without seeding production."""
import argparse
import io
import json
from pathlib import Path
import re

import httpx
from pypdf import PdfReader


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origin',required=True,choices=['https://finpilot-ai-sme-copilot.vercel.app','https://finpilot-ai-web.onrender.com'])
    args=parser.parse_args()
    base=args.origin
    checks=[]
    with httpx.Client(timeout=45,follow_redirects=False) as client:
        for name,path in [('health','/health/'),('landing','/'),('demo','/demo/personal/'),('personal CSS','/static/css/personal.css'),
            ('editable deck','/static/submission/finpilot-aignite-2026.html'),('PDF deck','/static/submission/finpilot-aignite-2026.pdf')]:
            response=client.get(base+path)
            assert response.status_code==200,(name,response.status_code)
            checks.append({'name':name,'status':response.status_code})
            if name=='demo':
                token=re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"',response.text).group(1)
                sticker='alt="Built For Ostad Presents YUNet AIgnite Buildathon 2026"' in response.text
            if name=='PDF deck':
                assert response.content.startswith(b'%PDF') and len(PdfReader(io.BytesIO(response.content)).pages)==5
            if name=='editable deck':
                assert response.text.count('<section class="slide')==5
        response=client.post(base+'/demo/personal/',data={'csrfmiddlewaretoken':token,'scenario':'delay','delay_days':'7','income_reference':'demo-income'},
            headers={'Origin':base,'Referer':base+'/demo/personal/'})
        assert response.status_code==200 and 'Baseline vs your scenario' in response.text and '2000.00' in response.text
        checks.append({'name':'stateless synthetic delayed-income comparison','status':200})
        response=client.get(base+'/demo/personal/?format=pdf')
        assert response.status_code==200 and response.content.startswith(b'%PDF')
        text=' '.join(p.extract_text() for p in PdfReader(io.BytesIO(response.content)).pages).replace(',','')
        assert '18000' in text and '6000' in text
        response=client.get(base+'/personal/new/')
        assert response.status_code==302 and '/login/' in response.headers['location']
        checks.append({'name':'private onboarding authentication','status':302})
    report={'origin':base,'checks':checks,'genuine_five_slide_pdf':True,'public_demo_financial_values_verified':True,
        'production_records_seeded':False,'financial_records_changed':False,'production_chat_changed':False,
        'official_sticker_present':sticker,'sticker_limitation':None if sticker else 'Original official image bytes not supplied; no replacement artwork used.'}
    output=Path('test-results/buildathon-production-'+('render' if 'onrender.com' in base else 'vercel')+'.json')
    output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))


if __name__=='__main__':
    main()
