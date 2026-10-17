# Benchmark failure analysis

Final weighted run: 147 passed, **25 partial**, 0 failed/blocked out of 172. A pass threshold of 0.80
allows omissions; do not say “172 passed”. Every sub-perfect dimension, even in a passing case,
is retained in `evaluation/final/divergences.json` with raw reason and provisional classification.
Combined labels deliberately preserve unresolved attribution; they are not a claim of adjudication.

## Remaining partial cases

DQ-004, EDGE-009, EXP-002, EXP-005, FIN-002, FIN-006, FIN-014, PAIR-01-A, PAIR-02-A, PAIR-03-A, PAIR-04-A, PAIR-06-A, PAIR-06-B, PAIR-08-B, PAIR-12-A, PAIR-12-B, PAIR-13-A, PAIR-14-A, PAIR-16-A, PAIR-17-A, PAIR-17-B, PAIR-18-A, PAIR-18-B, PAIR-20-B, REC-004.

## Main causes

1. **Unsupported/unexposed metrics (E).** Borrowing-limit booleans, reducible/restricted totals,
   split details, selected growth ratios and absent hypothetical financing terms are not all
   exposed by this adapter. We did not implement an oracle-shaped alternate financial engine
   to fill them. Missing values remain missing and lose credit.
2. **Wording/convention (C, sometimes B).** The policy scorer compares the first 40 normalized
   characters of violation strings. E.g. “tx:… protected payroll…” and “Payroll is protected…”
   can describe the same rejection but receive zero text coverage. Actual feasible sets and
   all 21 group relations still agree. The scorer is unchanged; no expected prose is echoed.
3. **Financing bases (C/E).** `repayment_total` in the benchmark means repayments inside the
   horizon; the app schedule exposes lifetime repayment. The current scalar adapter retains
   its lifetime value, explicitly documented as a remaining mapping divergence. Some reference
   calculations synthesize a gap loan even if borrowing is disallowed/no candidate is supplied;
   the adapter does not invent those terms. Multi-draw and ranking references require careful
   principal/rate/term inspection; raw finance terms are retained.
4. **Disclosure heuristics (C/E).** Keyword/number coverage is not semantic quality. Some
   disagreement is genuine missing context (e.g. affected currency row, restricted totals,
   half-cent explanation); some is phrasing. It remains scored down. No keyword stuffing.
5. **Benchmark gaps (B).** Upstream pair tables are expected-only, lifecycle outcomes are not
   scored, and pass-level adversarial scoring is not a complete natural-language safety test.
   Added actual-output sidecars rather than modifying expectations or presenting expected
   outcomes as observations. Seven literal lifecycle rejection-text differences remain visible.

## Confirmed application fixes (A)

Compound payroll labels could evade hard protection (PAIR-17-B); debt-service aliases could
under-report burden; future obligations beyond the horizon were invisible; generic blocking
messages failed to identify actual missing inputs. Fixed with independent regressions. Basic cash,
ROUND_HALF_UP, earned receivables, recurring deduplication and loan amortization were not rewritten.

## Test levels

| Level | Actually exercised | Does not establish |
|---|---|---|
| Oracle | original known-answer/invariant/schema/scenario tests | application performance |
| Services | 172 isolated cases, real ORM, state, issues, persisted investigations, scenarios, financing and memory | LLM reasoning or production runtime |
| Supplemental | 21 actual pair relations, 83 lifecycle assertions, rollback/ledger checks | semantic proof for arbitrary prose |
| Security regressions | cross-resource/tenant denials, viewer/CSRF/export boundaries, no-borrowing, stale acceptance, bounded inputs, mocked injection/tool failures | full pentest or live-provider safety |
| PostgreSQL concurrency | isolated import/accept/monitor tests in full app suite | deployment scheduler configuration |
| Browser | existing synthetic workflow + 63 Chromium responsive checks | all devices/browsers/accessibility certification |

Contradictory instructions and free-text requests to reuse old analysis are not equivalent to
supplying an actual persisted stale decision ID. They remain limited coverage; no fabricated
old record was injected to manufacture a pass. Deployment/provider/SMTP/scheduler not activated.
