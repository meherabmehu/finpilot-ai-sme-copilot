# AIgnite buildathon implementation and release evidence

Prepared 5 November 2026, Bangladesh time. Branch: `feat/finpilot-platform`.
Starting local and fetched remote HEAD: `34be3b073ff16a2761f2c1defa86d7b1361ca3b1`.
Existing project history and financial records are retained.

## A. Existing project audit

Reusable: Django authentication/memberships; one scoped financial ledger per workspace;
Decimal cash arithmetic and dated timelines; financial completeness/record bounds;
immutable saved scenarios and decisions; Groq structured evidence/conditional synthesis;
safe PDF/CSV/XLSX exports; CSRF, source fingerprints, rate limiting and browser tooling.
Existing Business Mode has five pages and six Planning tabs. It was preserved.

Missing at baseline: personal workspace identity, consumer onboarding and categories,
income/bill terminology, a future-income-excluding spending buffer, four consumer
what-ifs, an account-free stateless demo and buildathon presentation/submission assets.
Supplier recovery/loan underwriting tools were unsuitable as a default consumer UI.

Security constraints: financial data is user-provided, not bank-verified; never treat
pending income as paid cash, never mutate records in simulations, and never use one
workspace's records as another mode's AI context. Public demos must not share writable
financial state or spend unbounded provider quota. Actual provider credentials stay
server-side; a duplicate credential in the tracked example was removed without
changing the ignored local copy. No secrets are included in screenshots or submission.

## B. Meaningful new buildathon work

- `Business.mode` identifies Personal versus Business workspaces; migration
  `0006_personal_finance_mode` defaults every existing workspace to Business.
  `PersonalProfile` stores income type and optional savings target without moving cash.
- Dedicated personal setup collects cash, reserve, dated optional expected income and
  dated optional recurring essential bills. An amount cannot be supplied without its
  date. Due-today bills are entered as individual unpaid bills, not silently excluded
  from a future-only recurring projection.
- Consumer Dashboard shows paid available cash, bills, cash after bills excluding
  future receipts, emergency reserve, spending room, risk and next action.
- My Money uses personal categories and clearly separates received/paid from expected/
  unpaid records. It supports essentiality, void/edit, preferences and scoped recurring
  entries. Linking an individual bill to its recurring occurrence prevents duplication.
- Personal Planning compares 7/14/30-day selected-income delays, an explicit unexpected
  expense, a hypothetical savings transfer and 10/20/30% lower expected income.
  Saved comparisons retain their original source fingerprints and remain hypothetical.
- Private AI shares the existing Groq transport and validation while replacing SME
  source context/actions with consumer cash, bills, savings and actual dates.
- A public `/demo/personal/` works without credentials, shared database records or paid
  AI calls. Its explanations are explicitly deterministic. Its genuine synthetic PDF
  export has no private data. Authenticated workspaces use the real configured Advisor.
- Genuine personal PDF/CSV/XLSX reports include current cash, bill priorities, reserve
  assumptions and the ten most recent saved hypothetical comparisons.

## C. Financial and AI evidence

Synthetic known answer: 18,000 BDT paid cash + 10,000 expected in four days − 12,000
essential bills in seven days = 16,000 estimated ending cash. Without any future
receipts, after-bill cash is 6,000; an 8,000 reserve leaves **zero conservative spending
room**. Delaying the selected receipt seven days preserves 16,000 ending cash but
reduces the interim minimum to 6,000 and creates a 2,000 reserve gap.
Delaying it thirty days excludes it beyond the thirty-day horizon, leaving 6,000;
the income is explicitly not described as permanently lost.

Reducing future income by 10/20/30% gives 15,000/14,000/13,000 ending cash. An assumed
5,000 extra expense or savings transfer gives 11,000 under the baseline receipt dates;
this conditional scenario is not a claim that 5,000 is safe to spend before receipt.
Every scenario uses Decimal amounts and leaves actual records unchanged.

Real Personal Mode Groq inference with the marked synthetic local workspace was
validated in 1,106 ms; a genuine browser interaction also displayed a validated
Groq response. Financial source fingerprint remained unchanged. No real owner's data
was used for these external tests. Public demo explanations are never represented as
that real model execution. Model latency/quota and complete real-world advice quality
are not guaranteed by these individual tests.

## D. Consumer privacy and business regression

Workspace ownership/membership is checked before dispatch, reads and writes. Viewer
accounts cannot save scenarios/preferences. Consumer-mode record querysets remain
scoped to authorized accounts/recurrences; model output cannot select other workspace
IDs. Personal Mode bypasses the legacy SME tool path and cannot start an SME Decision
Lab investigation. Personal pages do not expose the SME loan-comparison workflow.

The old three-way cash, source consistency, recovery, debt, forecast and export logic
is retained for Business workspaces. Existing saved financial decisions are untouched.
No personal fixtures are seeded into production or real owner accounts.

## E. Official sticker: exact asset remains required

The attached visual reference was inspected: a wide white/purple/orange “Built For”
sticker with Ostad/YUNet/AIgnite artwork, displayed at 1600 × 567 in chat. The supplied
attachment directory contains only `Pasted text.txt`; no original image file bytes
were available in the workspace/attachment search. The official event header image
found online has a different shape and was **not substituted**.

Prepared directory: `static/buildathon/`. Intended filename:
`yunet-aignite-buildathon-2026-sticker.png`, or the original `.jpg`/`.jpeg`/`.webp`.
The shared context processor enables the exact asset only when it actually exists.
The top strip is wired into public landing, authenticated app, personal onboarding and
public demo, with `height:auto`, no cropping, dedicated spacing and meaningful alt text.

**Not completed:** original file format/transparency/hash verification and actual
sticker visual/readability checks. No replacement artwork, stretched logo, empty
image or false “sticker integrated” claim was added. A local filename does not recover
an inline image's original bytes. Supply the original file before final submission;
then rerun all seven-width visibility checks and deploy the actual asset.

## F. Validation

Full-suite and browser artifacts are stored in ignored `test-results/`:

| Check | Evidence |
|---|---|
| Django / migration consistency / Ruff | `manage.py check`, `makemigrations --check --dry-run`, `python -m ruff check .` |
| Full SQLite suite | **366 passed, 2 PostgreSQL-only skips**; `buildathon-sqlite.xml` |
| Full disposable PostgreSQL suite | **368 passed, no skips**; `buildathon-postgres.xml`; isolated marked loopback cluster, never production |
| Consumer regressions | `tests/test_personal_mode.py`: independent amounts, received versus expected income, zero/negative cash, completeness, invalid amounts, ownership, viewer/CSRF, scope, actual paid updates, genuine exports |
| New browser workflow | `buildathon-browser/verification.json`: 56 page/width checks across 320,375,390,768,1024,1440,1920; 16 axe audits; private onboarding, saved scenario, actual income, three exports |
| Existing Business browser | `survival/verification.json`: 147 viewport checks, 21 exports, 18 axe audits; financial records unchanged |
| Real Groq | `buildathon-groq.json`; only marked synthetic personal records |
| Editable deck / PDF | `static/submission/finpilot-aignite-2026.html` and `.pdf`; real five-page PDF, working synthetic screenshots |

The first full runs hit four stale Windows scratch-directory ACL errors. Fresh,
uniquely named scratch/cache directories fixed the test environment; no failing test
was removed or skipped. Initial browser contrast findings on the teal highlight and
onboarding help text were fixed; affected audits were rerun. Final counts are above; post-deployment results are recorded in the release handoff/addendum.
The original 172-case SME benchmark was also rerun on an isolated database: 157 pass,
15 partial, zero failed/blocked, weighted 0.928124. This is SME regression evidence,
not a claim that the SME benchmark validates new consumer functionality.

## G. Submission materials and operations

- [Devpost-ready content and manual checklist](BUILDATHON_SUBMISSION.md).
- [English 2–3 minute demo script](BUILDATHON_VIDEO_SCRIPT.md). No video was recorded.
- Five-slide editable HTML and genuine PDF live under `static/submission/`.
  Reproduce with `python scripts/export_buildathon_deck.py`; exactly five pages are
  checked with pypdf. Slides 3 and 5 plus mobile/desktop app screenshots were inspected.
- Developer introduction uses the verified repository handle `meherabmehu`, not
  invented qualifications or student status. Confirm participant details manually.
- The live app retains existing Render/Vercel configuration, private credentials and
  database. Approved build/start commands apply additive migration 0006 and print its
  applied status. No hosted seeding, test accounts, financial reset or email changes.
- Production checks use public synthetic requests and existing authorized read-only
  Business pages. Creating a new private consumer account/data in production is not
  part of the smoke test. New-account email delivery remains operator-dependent.

## H. Readiness limits

This is an implemented consumer workflow and tested SME-preserving extension, not a
claim of complete competition submission. **Official sticker file integration remains
blocked by missing original bytes.** Confirm registration/eligibility and the earlier
5 November 10 PM Bangladesh platform deadline. No Devpost submission, video upload or
presentation-platform upload has been made. The public deck URL is a hosted file,
not evidence that a Devpost entry was submitted. Automatic alerts, bank connections,
trained personal forecasts and automatic partial-settlement matching were not added.

## I. Verified live release — 5 November 2026

Implementation commit `1d56892151dd681675728a982399d6b8c207949c` and submission
materials commit `24d71fae270c5150d7630e5599a90130ea1c60c4` were pushed to
`feat/finpilot-platform`. Both providers deployed the latter release:

- Render deployment `dep-dblng7vb9u1s73d2msbg` reached `live`.
- Vercel production deployment reached `Ready`.
- Both providers' startup/build logs confirmed `[X] 0006_personal_finance_mode`.
- Public smoke checks on both origins passed: health, landing, Personal demo,
  consumer CSS, editable five-slide deck, genuine five-page PDF, CSRF-protected
  synthetic delayed-income comparison, synthetic PDF values and private-onboarding
  authentication redirect. No production financial records or chats were written.
- Both providers' authenticated read-only smoke passed all 12 existing Business pages and
  recognized the configured AI provider. This badge is configuration evidence;
  actual Groq inference was verified separately on isolated synthetic local data.

Render initially exceeded the smoke clients' 40/45-second request timeouts. Runtime
logs showed the free service starting again, applying no pending migrations and
booting Gunicorn successfully. A subsequent health request returned 200 and the
complete public smoke rerun passed. Initial timeout results are not counted as
passes; first requests after idle may still be slow.

Live origins: <https://finpilot-ai-web.onrender.com> and
<https://finpilot-ai-sme-copilot.vercel.app>. Public demo: `/demo/personal/`.
Presentation: `/static/submission/finpilot-aignite-2026.pdf`, editable `.html`
beside it. Ignored release evidence: `buildathon-production-render.json`,
`buildathon-production-vercel.json`, `final-production-render.json` and `final-production-vercel.json` under
`test-results/`.

The exact sticker filename and installation instructions are recorded in
`static/buildathon/README.md`. Original artwork bytes are still absent; both live
checks correctly report `official_sticker_present: false`. The asset and its actual
visual checks remain outstanding, along with the manual submission steps in section H.
