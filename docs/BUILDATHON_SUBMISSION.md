# FinPilot AI — YUNet AIgnite 2026 submission

## Verified competition requirements

Official [rules](https://yunet-aignite26.devpost.com/rules) permit an existing project
when meaningful improvements are made specifically for this buildathon. This release
adds actual Personal Mode, conservative consumer calculations, four personal scenario
types and an account-free synthetic demo to the existing SME project; these were not
present at baseline `34be3b073ff16a2761f2c1defa86d7b1361ca3b1`.

Use **5 November 2026, 10:00 PM Bangladesh time (UTC+06)** as the submission cutoff.
The [official schedule](https://yunet-aignite26.devpost.com/details/dates) and page
header show 10 PM; the prose rules say 11:59 PM. Follow the earlier platform cutoff.
Solo participation and current Bangladesh student eligibility must be confirmed by
the owner. Registration/eligibility has not been inferred from an email address.

## Devpost-ready content

**Title:** FinPilot AI — Personal & Micro-Business Financial Survival Copilot

**Tagline:** Plan around irregular income, essential bills and your emergency reserve.

**Problem:** A student, freelancer or individual seller can have enough expected
monthly income and still run short before a bill deadline. An unpaid promise is not
money available to spend. Simple monthly totals can hide that timing problem.

**Solution:** A personal workspace separates received cash, expected income, essential
bills and savings goals. A conservative spending buffer excludes all future receipts.
Users compare dated scenarios before acting, ask a grounded AI Advisor and export
their own financial snapshot. Existing business workspaces retain their SME tools.

**Key features:** Short personal onboarding; cash/bill/reserve dashboard; received versus
expected records; essential bill priorities; 7/14/30-day income delays; unexpected
expenses; savings-transfer assumptions; 10/20/30% future-income reductions; historical
saved comparisons; genuine PDF/CSV/XLSX reports; separate personal/business workspaces.

**Technologies:** Django, PostgreSQL (SQLite locally), Python Decimal, Django templates,
Tailwind and scoped CSS, vanilla JavaScript, Chart.js, Groq's OpenAI-compatible API,
Pydantic schemas, Playwright and axe-core; existing Vercel/Render hosting.

**Meaningful AI:** The private Advisor uses the selected workspace's authorized
financial evidence. Groq selects relevant sources and can generate labeled conditional
reasoning; dates and amounts come from deterministic calculations. Invalid output is
rejected, outages use truthful fallback, and AI cannot alter the ledger. A real Groq
call and browser response were verified using only an isolated synthetic Personal
Mode workspace. The account-free public demo deliberately uses deterministic
explanations and never spends shared API quota; it is not described as live AI.

**Innovation:** The same ending balance can hide different interim risk. In the
synthetic example, delaying a 10,000 BDT receipt by seven days preserves 16,000 BDT
ending cash but creates a 2,000 BDT emergency-reserve shortfall before the bill is due.
This connects consumer decisions to transparent, dated financial evidence.

**Challenges:** Reusing a mature SME ledger without exposing inappropriate supplier
or underwriting concepts to consumers; separating expected money from paid cash;
keeping simulations read-only; validating AI output and preserving workspace isolation.

**Accomplishments:** A complete personal setup → dashboard → scenario → private
Advisor → report workflow; stateless public demo; real provider verification; existing
business tests retained; tested mobile/tablet/desktop layouts; a real five-page PDF deck.

**Future improvements:** Bank imports with explicit consent, richer personal budget
categories, independently evaluated forecast calibration, automatic monitoring with
delivery evidence, and a verified linked partial-settlement workflow. These are not
claimed as implemented features.

**Public app:** https://finpilot-ai-sme-copilot.vercel.app/

**Account-free demo:** https://finpilot-ai-sme-copilot.vercel.app/demo/personal/

**Presentation PDF:** https://finpilot-ai-sme-copilot.vercel.app/static/submission/finpilot-aignite-2026.pdf

**Editable HTML deck:** `static/submission/finpilot-aignite-2026.html` (exactly five slides).
The PDF is genuinely rendered from this source, with screenshots of working synthetic
workspaces.

**PowerPoint:** `static/submission/finpilot-aignite-2026.pptx` (five slides).
Cover presenter text is editable; remaining slide content preserves the HTML design
as rendered images. Regenerate with `scripts/export_buildathon_deck.py`, then
`scripts/export_buildathon_powerpoint.py` (optional local `python-pptx` dependency).

**Repository:** https://github.com/meherabmehu/finpilot-ai-sme-copilot

**Developer:** Md. Meherab Hossain Talukder — Solo Participant.
Repository identity: `meherabmehu`. Name and participation label supplied by the owner.

**Optional video:** Not recorded or uploaded. Use [the English script](BUILDATHON_VIDEO_SCRIPT.md).

## Manual submission checklist

1. Confirm student eligibility, registration and your Devpost participant details.
2. Official sticker is now included as the original, unmodified 1600×567 JPEG at
   `static/buildathon/yunet-aignite-buildathon-2026-sticker.jpeg`.
3. Local browser verification passed all 28 sticker checks: landing, demo,
   authenticated onboarding and dashboard across seven widths, with preserved aspect
   ratio, successful image loading, visible top placement and no horizontal overflow.
4. Open the public demo and PDF link on an incognito/mobile browser after deployment.
   Confirm you can explain the difference between public deterministic demo and
   authenticated real AI. Email activation for new private accounts requires working
   operator email delivery; the public demo needs no credentials.
5. Upload the five-slide PDF or supply its verified public link. Add only an actual
   video URL if you record/upload one. Submit manually before the earlier 10 PM cutoff.

No Devpost entry, registration, mail, video or presentation upload has been submitted
on the owner's behalf. The original sticker has now been supplied and integrated;
registration, eligibility and the final Devpost submission remain manual steps.
