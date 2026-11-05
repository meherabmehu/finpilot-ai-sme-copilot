"""Package real synthetic-workspace screenshots as 3:2 Devpost gallery images.

Uses the existing local browser-verification screenshots for the business/mobile
views. Run those verifications first if their ignored test-results files are absent.
No AI-generated UI, financial writes, or image retouching is performed.
"""
import html
import json
from pathlib import Path
import shutil
import zipfile

from PIL import Image
from playwright.sync_api import sync_playwright


def main():
    output = Path('static/submission/devpost-gallery')
    output.mkdir(parents=True, exist_ok=True)
    thumbnail = Path('static/submission/finpilot-thumbnail.png')
    shutil.copyfile(thumbnail, output / '01-finpilot-cover.png')
    entries = [
        ('02-personal-dashboard', 'Know what is available to spend.',
         'Separate paid cash, upcoming bills and your emergency reserve.',
         Path('static/submission/images/personal-dashboard.png'), False),
        ('03-payment-delay-scenario', 'Same ending balance. Different risk.',
         'A seven-day income delay reveals a BDT 2,000 interim reserve gap.',
         Path('static/submission/images/personal-scenario.png'), False),
        ('04-explainable-ai-advisor', 'AI guidance you can question.',
         'Actual saved Groq response with evidence references and explicit assumptions.',
         Path('static/submission/images/personal-advisor-excerpt.png'), False),
        ('05-small-business-dashboard', 'Protect the next essential payment.',
         'Business Mode surfaces dated cash risk, protected payments and overdue collections.',
         Path('test-results/survival/dashboard-1440.png'), True),
        ('06-mobile-personal-mode', 'A clearer money plan, on your phone.',
         'Actual mobile viewport: the same private Personal Mode workflow.',
         Path('test-results/sticker/dashboard-390.png'), False),
    ]
    work = Path('test-results/devpost-gallery')
    work.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='chromium')
        page = browser.new_page(viewport={'width':1536, 'height':1024},device_scale_factor=1)
        for filename, title, subtitle, source, crop in entries:
            assert source.is_file(), source
            mobile = 'mobile' in filename
            image_class = 'viewport' if crop else 'contain'
            content = f'''<!doctype html><html><head><meta charset="utf-8"><style>
            *{{box-sizing:border-box}}body{{margin:0;width:1536px;height:1024px;background:#f0f7f7;color:#142d42;font-family:Arial,sans-serif;padding:46px 64px}}
            .brand{{font-size:19px;color:#087c70;font-weight:700;letter-spacing:2px}}h1{{font-size:43px;line-height:1.12;margin:15px 0 10px;letter-spacing:-1px}}p{{font-size:23px;color:#4c6676;margin:0 0 24px;line-height:1.35}}
            .frame{{height:728px;background:#fff;border:1px solid #d7e5e6;border-radius:18px;overflow:hidden;display:flex;align-items:center;justify-content:center;box-shadow:0 12px 36px #12334012}}
            .frame img.contain{{width:100%;height:100%;object-fit:contain}}.frame img.viewport{{width:100%;height:auto;align-self:flex-start}}
            .mobile{{display:flex;gap:64px;align-items:center;justify-content:center;width:100%;height:100%;padding:16px 48px;background:#e7f3f0}}
            .mobile img.contain{{height:690px;width:auto;flex:none;border-radius:18px;border:1px solid #c4d7d7;box-shadow:0 16px 40px #153c4b22}}.mobile aside{{max-width:540px}}.mobile h2{{font-size:42px;line-height:1.18;margin:0 0 28px}}.mobile p{{font-size:27px;line-height:1.55}}
            footer{{font-size:16px;color:#4c6676;display:flex;justify-content:space-between;margin-top:20px}}
            </style></head><body><div class="brand">FINPILOT AI · FINANCIAL SURVIVAL COPILOT</div><h1>{html.escape(title)}</h1><p>{html.escape(subtitle)}</p><div class="frame">'''
            image = f'<img class="{image_class}" src="{source.resolve().as_uri()}" alt="Actual application screenshot with synthetic records">'
            if mobile:
                content += '<div class="mobile">'+image+'<aside><h2>Your cash.<br>Your bills.<br>Your next decision.</h2><p>See paid cash separately from expected income.</p><p>Compare scenarios before acting.</p><p>Keep personal and business workspaces separate.</p></aside></div>'
            else:
                content += image
            content += '</div><footer><span>Actual application capture · synthetic workspace · presentation framing only</span><span>Md. Meherab Hossain Talukder · Solo Participant</span></footer></body></html>'
            document = work / f'{filename}.html'
            document.write_text(content, encoding='utf-8')
            page.goto(document.resolve().as_uri())
            page.locator('img').evaluate('(el)=>el.decode()')
            assert page.evaluate('document.documentElement.scrollHeight<=1024 && document.documentElement.scrollWidth<=1536')
            page.screenshot(path=str(output / f'{filename}.png'))
        browser.close()
    files = sorted(output.glob('*.png'))
    assert len(files) == 6
    manifest = []
    for path in files:
        with Image.open(path) as image:
            assert image.size == (1536, 1024)
        assert path.stat().st_size < 5_000_000
        manifest.append({'filename':path.name,'width':1536,'height':1024,'bytes':path.stat().st_size})
    archive = Path('static/submission/finpilot-devpost-gallery.zip')
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in files:
            bundle.write(path, path.name)
    (work/'verification.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None and len(bundle.namelist()) == 6
    print(json.dumps({'images':manifest,'zip':str(archive),'zip_bytes':archive.stat().st_size}))


if __name__ == '__main__':
    main()
