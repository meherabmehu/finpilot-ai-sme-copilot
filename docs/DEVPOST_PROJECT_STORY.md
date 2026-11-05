# FinPilot AI – Financial Survival Copilot

Copy the following story into Devpost's **About the project** field, starting with
`## Inspiration`. The tags and links after the story belong in their separate fields.

---

## Inspiration

A freelancer can have a payment on the way and still struggle to cover a bill due
tomorrow. A small business can show a healthy monthly total while running short of
cash before an essential payment. The problem is not only how much money is
expected, but **when it becomes available**.

I built FinPilot AI around a practical question: **“Can I make this decision now
without putting my next essential payment or emergency reserve at risk?”**

For this buildathon, I extended my existing small-business financial application
with a dedicated consumer experience for freelancers, students and individual
sellers. Personal finances deserve their own workflow, rather than a business
dashboard with a different label.

## What it does

FinPilot AI helps users understand their cash position, explore possible shortages
and compare decisions before acting.

- **Personal Mode** separates paid cash, expected income, upcoming essential bills
  and an emergency reserve. Its conservative spending buffer excludes future
  receipts until they actually arrive.
- **Scenario planning** compares a baseline with delayed income, an unexpected
  expense, a proposed savings transfer or lower future income. Simulations remain
  hypothetical and do not change actual financial records.
- **The private AI Advisor** explains authorized financial evidence, identifies
  assumptions and offers conditional guidance. Financial amounts are calculated
  deterministically; the AI cannot execute transactions or move money.
- **Business Mode** preserves the existing tools for cash planning, payment
  priorities, overdue collections and financial reports.
- **Reports and separate workspaces** help users review their records while keeping
  personal and business contexts apart.

An account-free demo lets judges explore the consumer workflow using clearly
labeled synthetic data. Its explanations are deterministic; private workspaces use
the configured Groq integration.

## How I built it

I developed FinPilot AI as a solo participant using **Python, Django and
PostgreSQL**, with Django templates, Tailwind CSS, JavaScript and Chart.js for the
interface. Python's Decimal arithmetic supports financial calculations, and
structured Pydantic schemas help validate AI output.

The core flow is **records → dated cash calculations → scenario comparison →
evidence-based explanation → user decision**. Groq adds explanations around
authorized evidence rather than acting as the source of financial figures. If
provider output is invalid or unavailable, the application falls back to a
truthfully labeled calculated explanation.

The buildathon work adds consumer onboarding, Personal Mode, conservative spending
and savings calculations, four personal scenario types, consumer-specific AI
context and a stateless public demo. I reused the existing ledger, authentication,
workspace controls and export safeguards instead of rebuilding them.

The application is deployed on Render and Vercel with its backend and database
connection. Screenshots and public demo examples use synthetic records.

## Challenges I faced

The hardest design challenge was separating **expected money from available cash**.
Counting an unpaid invoice as spendable would make the interface reassuring while
making its advice less useful.

Another challenge was extending a mature business workflow without bringing
supplier, payroll or lending assumptions into personal planning. I added
mode-specific forms, views and explanations while preserving existing business
behavior.

AI reliability also required clear boundaries: workspace isolation, validated
evidence references, explicit uncertainty and a fallback that does not pretend a
model answered when it did not. Finally, financial tables and explanations needed
to remain usable on phones as well as desktop screens.

## Accomplishments I am proud of

One synthetic example demonstrates the project's central idea: delaying a
**BDT 10,000** receipt by seven days leaves ending cash at **BDT 16,000**, yet creates
an interim **BDT 2,000 emergency-reserve shortfall**. The monthly ending balance
alone misses that risk.

I completed the personal setup, dashboard, scenario, private Advisor and reporting
workflow, verified an actual Groq response using isolated synthetic records, and
retained existing business regression coverage. The PostgreSQL suite passed
**368 tests**, with additional browser checks across seven screen widths.

## What I learned

Financial guidance becomes more useful when it explains timing and assumptions,
not just a final number. Clear separation between received cash, uncertain income
and hypothetical decisions matters as much as the model itself.

I also learned to evaluate the complete workflow: calculations, authorization,
fallback behavior, exports and responsive presentation. A fluent explanation is
only one part of a trustworthy financial tool.

## What's next for FinPilot AI

Next steps include consent-based bank imports, richer personal budgeting,
independently evaluated forecast calibration and opt-in monitoring with verified
notification delivery. These are future improvements, not features claimed in the
current release.

FinPilot AI provides decision support based on recorded data and assumptions. Its
projections are conditional estimates, not guarantees.

---

## Built with — separate Devpost tags

Python, Django, PostgreSQL, Groq, Pydantic, Tailwind CSS, JavaScript, HTML5, CSS3,
Chart.js, Playwright, Render, Vercel, ReportLab, openpyxl, GitHub

## Try it out — separate Devpost links

- Account-free demo: https://finpilot-ai-web.onrender.com/demo/personal/
- Live application: https://finpilot-ai-web.onrender.com/
- Alternative deployment: https://finpilot-ai-sme-copilot.vercel.app/
- Source code: https://github.com/meherabmehu/finpilot-ai-sme-copilot
- Presentation PDF: https://finpilot-ai-web.onrender.com/static/submission/finpilot-aignite-2026.pdf
- PowerPoint: https://finpilot-ai-web.onrender.com/static/submission/finpilot-aignite-2026.pptx

## Image gallery upload instructions

Download and extract `static/submission/finpilot-devpost-gallery.zip`, then upload
the six PNG images individually in numbered order. Devpost's image field accepts
the extracted images, not the ZIP archive. Each is 1536×1024 (3:2), below 5 MB.

1. Cover illustration — generated marketing artwork; also suitable as the thumbnail.
2. Personal dashboard — actual application, synthetic workspace.
3. Payment-delay comparison — actual scenario result, synthetic records.
4. AI Advisor — actual saved Groq response excerpt; presentation typography enlarged.
5. Small-business dashboard — actual dashboard viewport, synthetic test workspace.
6. Mobile Personal Mode — actual phone viewport with explanatory presentation text.

**Participant:** Md. Meherab Hossain Talukder — Solo Participant.
No submission, registration or video upload is performed by this document.
