# Agentic evaluation results — actual local Django services

All figures are synthetic. Tested application/adapter source commit: `a283348` on `feat/finpilot-platform`.
Final report UTC dates fall on 17 October 2026; user-local date is 18 October. Environment manifests
record Python/Django versions, source hashes, application SHA and clean code tree. PostgreSQL 17.11,
private Unix socket, a fresh random database per CLI invocation, individual case rollbacks, final drop.
No production, provider, external notification or payment system was contacted.

## Initial vs final

Initial application code `c211b31`, new adapter before app fixes: 172 selected, 171 executed,
133 passed, 38 partial, 0 failed, 1 blocked (PAIR-17-B), 0 detected critical failures. Overall NOT
reportable; **0.881848 is only the executed-subset mean**. SQLite's extreme monetary boundary
is a separate backend limitation; the valid comparison uses PostgreSQL throughout.

Controlled post-application-fix run with the same adapter: 172 executed, 147 passed, 25 partial,
0 failed/blocked, score 0.915639. Final adapter assurance (explicit supplied finance terms and
actual oversized-input probes) gives **0.917476**, with the same 147/25 counts. Do not attribute
that small adapter effect to improved application arithmetic. Earned revenue and loan formulas
were NOT changed. **Weighted score is not prediction accuracy or an LLM capability score.**

| Category | Initial pass/partial/blocked | Final pass/partial/blocked | Final weighted mean |
|---|---:|---:|---:|
| adversarial | 20/2/0 | 22/0/0 | 0.962391 |
| business_policies | 21/18/1 | 23/17/0 | 0.872339 |
| data_quality | 17/1/0 | 17/1/0 | 0.933549 |
| decision_memory | 14/0/0 | 14/0/0 | 0.951207 |
| edge_cases | 16/2/0 | 17/1/0 | 0.948572 |
| expenses | 7/3/0 | 8/2/0 | 0.901708 |
| financing | 8/6/0 | 11/3/0 | 0.861827 |
| liquidity | 19/5/0 | 24/0/0 | 0.920145 |
| receivables_payables | 11/1/0 | 11/1/0 | 0.948214 |

## Actual CLI suites

| Suite | Selected/executed | Pass | Partial | Failed/blocked | Weighted score |
|---|---:|---:|---:|---:|---:|
| core | 78/78 | 71 | 7 | 0/0 | 0.918192 |
| policy | 40/40 | 23 | 17 | 0/0 | 0.872339 |
| counterfactual | 145/145 | 122 | 23 | 0/0 | 0.915314 |
| financing | 14/14 | 11 | 3 | 0/0 | 0.861827 |
| data_quality | 18/18 | 17 | 1 | 0/0 | 0.933549 |
| adversarial | 22/22 | 22 | 0 | 0/0 | 0.962391 |
| decision_memory | 14/14 | 14 | 0 | 0/0 | 0.951207 |
| full | 172/172 | 147 | 25 | 0/0 | 0.917476 |

All eight exited 0 under upstream semantics: no failed/blocked case. Exit 0 does NOT mean every
case passed. Suites overlap; never sum their denominators. All reports validate unchanged upstream
JSON schema. Zero detected critical classes in every final suite is a narrow pattern-based result,
not a security certification. Full denominator is 172, including 25 partial outcomes.

## Additional checks the upstream score does not perform

- 21/21 actual-output pair/family relations hold (20 two-member pairs + LIQ-005 three-member family).
- 14 actual lifecycle scripts: 83 literal assertions, 76 match, 7 rejection-message wording differences;
  zero state/outcome/non-wording mismatches. All seven expected rejections actually occurred.
- Cleanup confirmed for 172/172 cases; zero detected application accounting-row mutations.
- Actual responses, traces, refusals and lifecycle output: `evaluation/final/*actual-responses.json`.
- Supplemental results remain separate and never alter upstream scores/expectations.

## Standalone authority verification

Original package: 978 passed / 1 skipped (optional prior reproduction); 172 scenario files validated,
including schema, required elements, synthetic declarations, oracle reproduction and differentiations.
Reference: 172 passed, 0.986261, self-consistency only. Negative control: 172 failed, 0.0, ten critical
classes. Neither is a FinPilot result. Source archives/CRC/hash manifest: `evaluation/archive-verification.json`.

## Interpretation and remaining work

Read `BENCHMARK_FAILURE_ANALYSIS.md` and `FINANCIAL_ORACLE_DIVERGENCES.md` before quoting the score.
The upstream pair and lifecycle tables contain EXPECTED data, not measured responses. The real
comparison is in `*.supplemental.json`. Some natural-language adversarial demands (contradictions,
old analysis references without supplied IDs) are not fully exercised by the weighted scorer;
existing service regressions test stale IDs, role checks, no-borrowing and retry guards separately.
Live LLM behavior, deployed scheduler, production runtime, broader penetration testing, source-data
vendor redistribution rights and forecast accuracy remain unverified. Git delivery is reported
separately: commits are local until a secure GITHUB_TOKEN is supplied and a normal push succeeds.

## Final application verification

- SQLite: **179 passed / 2 PostgreSQL-only skipped**, 41.79 s.
- Isolated UTF-8 PostgreSQL 17: **181 passed / 0 skipped**, 44.78 s, including concurrency tests.
- Django system and DEBUG=false deployment-configuration checks: passed (local test configuration only).
- Migration drift: none. Ruff, frontend build and collectstatic: passed.
- Chromium synthetic workflow: **63 checks**, zero page overflow / JavaScript errors.
- Nine committed initial/final machine reports validate the original result schema. Independent final
  replay has identical summary/category scores. Source hash pinning rejects edited evaluators.
- Test databases removed; no persistent evaluator process or automatic scheduler required.

Code milestones: `3e74f8d` isolated adapter/baseline; `ac4663b` confirmed protection/transparency fixes;
`a283348` actual pair/lifecycle evidence and source pinning. Documentation/report delivery is a separate
commit. Normal public fetch confirms remote branch ancestry; **no push was attempted without the
required securely configured GITHUB_TOKEN**. No credentials appear in repository files or remote URL.
