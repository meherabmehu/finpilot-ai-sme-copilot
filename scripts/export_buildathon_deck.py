"""Export the editable five-slide HTML deck with the existing Playwright toolchain."""
from pathlib import Path
from playwright.sync_api import sync_playwright
from pypdf import PdfReader


def main():
    source=Path('static/submission/finpilot-aignite-2026.html').resolve()
    destination=source.with_suffix('.pdf')
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='chromium')
        page=browser.new_page(viewport={'width':1280,'height':720})
        page.goto(source.as_uri())
        page.evaluate('document.fonts.ready')
        assert page.locator('section.slide').count()==5
        overflow=page.locator('section.slide').evaluate_all('(slides)=>slides.map(s=>({id:s.id,overflow:s.scrollHeight>s.clientHeight+1}))')
        assert not any(s['overflow'] for s in overflow),overflow
        page.pdf(path=str(destination),width='1280px',height='720px',print_background=True,prefer_css_page_size=True)
        output=Path('test-results/buildathon-slides')
        output.mkdir(parents=True,exist_ok=True)
        for index,slide in enumerate(page.locator('section.slide').all(),1):
            slide.screenshot(path=str(output/f'slide-{index}.png'))
        browser.close()
    assert len(PdfReader(destination).pages)==5
    print('Editable HTML deck and genuine 5-page PDF generated; five slide screenshots saved.')


if __name__=='__main__':
    main()
