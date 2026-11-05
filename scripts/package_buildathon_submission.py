"""Build the judge upload from an explicit public-file allowlist, below 35 MB."""
from pathlib import Path
import zipfile

from pypdf import PdfReader


def main():
    root = Path('static/submission')
    pdf = root / 'finpilot-aignite-2026.pdf'
    powerpoint = root / 'finpilot-aignite-2026.pptx'
    assert len(PdfReader(pdf).pages) == 5
    brief = '''FINPILOT AI – FINANCIAL SURVIVAL COPILOT

Participant: Md. Meherab Hossain Talukder
Participation: Solo Participant

PRODUCT BRIEF
FinPilot AI helps freelancers and small business owners understand available cash,
anticipate possible shortages and compare decisions before acting. Personal Mode
separates received cash, expected income, essential bills and emergency reserves.
Users can simulate income delays, unexpected expenses, proposed savings transfers
and lower future income without changing actual records. The private Groq-powered
Advisor explains authorized evidence; deterministic calculations supply the numbers.
Existing Business Mode supports cash planning, payment priorities and reports.

JUDGE QUICK START
1. Open the account-free demo below. No credentials are required.
2. Select a seven-day income delay and compare baseline versus simulated results.
3. In the synthetic example, ending cash remains BDT 16,000 while a BDT 2,000
   interim reserve shortfall appears. Future receipts are not spendable cash.
4. Review the attached five-slide PDF. The PPTX contains the same five slides;
   its cover presenter text is editable and other content uses rendered slide images.

LINKS
Account-free demo: https://finpilot-ai-web.onrender.com/demo/personal/
Live app: https://finpilot-ai-web.onrender.com/
Alternative deployment: https://finpilot-ai-sme-copilot.vercel.app/
Repository: https://github.com/meherabmehu/finpilot-ai-sme-copilot
PDF: https://finpilot-ai-web.onrender.com/static/submission/finpilot-aignite-2026.pdf

IMPLEMENTATION AND VALIDATION
Python, Django, PostgreSQL, Decimal calculations, Pydantic, Tailwind CSS,
JavaScript, Chart.js and Groq. Consumer workflow added to the existing SME app.
368 PostgreSQL tests passed; browser checks covered seven viewport widths.
Actual Groq execution was verified with isolated synthetic personal records.

DEMO BOUNDARIES
The public demo uses deterministic explanations and synthetic data, not public
paid AI inference. Private workspaces use the configured Groq integration with
validated evidence and a calculated fallback. Projections depend on recorded data
and assumptions; AI cannot execute transactions or move money. Screenshots use
synthetic workspaces. No administrative credentials or secrets are included.

CONTENTS
01-finpilot-presentation.pdf — five slides, primary presentation
02-finpilot-presentation.pptx — same five slides, PowerPoint format
03-project-story.md — project inspiration, implementation, challenges and learning
README.txt — this brief and judge access instructions
'''
    destination = root / 'finpilot-submission-package.zip'
    with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(pdf, '01-finpilot-presentation.pdf')
        archive.write(powerpoint, '02-finpilot-presentation.pptx')
        archive.write(Path('docs/DEVPOST_ABOUT_THE_PROJECT.md'), '03-project-story.md')
        archive.writestr('README.txt', brief)
    assert destination.stat().st_size < 35_000_000
    with zipfile.ZipFile(destination) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist()) == {
            '01-finpilot-presentation.pdf', '02-finpilot-presentation.pptx',
            '03-project-story.md', 'README.txt',
        }
    print(f'Judge upload ready: {destination} ({destination.stat().st_size:,} bytes); four public files, five-slide presentation.')


if __name__ == '__main__':
    main()
