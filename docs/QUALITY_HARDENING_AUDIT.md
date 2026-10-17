# Quality hardening audit

## Baseline
- Existing checkout and branch preserved: feat/finpilot-platform at 3fd006e0798bc43e10a70dae6b94782084a8b102. Public fetch confirms same remote HEAD; no newer work. origin configuration was missing from the workspace snapshot and restored to the user-supplied existing URL; no repository/branch was created.
- Initial commands could not execute because installed dependencies are not persisted. Installed requirements, npm ci/build and collectstatic, then ran Django check, migration drift check, pytest and Ruff: **124 passed**, checks clean, no migration changes.

## Confirmed findings from code (before changes)
- Repeat identical files reuse DataImport by business/digest; confirmed files return zero on confirmation. Actual duplication from the reported identical-file retry is NOT established. Preview wording incorrectly says nothing is added until confirmation even for already confirmed files.
- Digest uniqueness and confirmation row locks exist. Preview creation races can surface IntegrityError. Confirmation service itself lacks reauthorization/business-level serialization (view does provide both). Cross-file content fingerprints reject ambiguous equal rows; reference correction semantics are not defined. Corrected amount with the same reference can bypass content identity.
- Pending earned receivables increase revenue but not paid cash: consistent with the existing recorded/earned operating basis, NOT a financial arithmetic bug.
- Question context recognizes payroll/supplier/date but not overdue collections, expense-growth evidence or explicit no-borrowing intent. Responses are generic.
- Scenario feasibility is action-constraint validity, not reserve-goal satisfaction. Ranking already explicitly means best among evaluated plans. Reduction suggestions include inventory without confirmed adjustability; dependencies exist but need stronger presentation.
- Forecast adds pending and recurring occurrences independently: explicitly linked occurrences can be double-counted. Historical baseline overlap is already disclosed, not proof that every forecast is duplicated. Weekly backtest uses a 60-day baseline unlike forecast's 90-day basis and net-cash WAPE can have a small denominator. The reported specific MAE/WAPE cannot be independently reproduced without that exact local dataset.
- Manual loan calculator uses user fees; products use LoanProduct.fee, so differing totals can be valid. Formula correction is not justified without independent oracle evidence. Labels do not clearly separate financing cost and total repayment.
- Reports emit raw dictionary strings, and XLSX casts all cells to text. These are confirmed presentation/type weaknesses.

## Planned safe checkpoints
B: clarify repeats and correction/identity semantics, lock and reauthorize import services, retain validation; document earned vs cash basis.
C/D: deterministic intent-specific evidence/collection assumptions and no-borrowing filter; explicitly separate action feasibility and reserve outcome.
E: deduplicate linked forecast schedules and improve reliability disclosures/backtest definitions; reconcile financing labels/inputs without changing amortization.
F/G/H: professional report sections, typed safe spreadsheet values, isolated PostgreSQL concurrency tests if available, security coverage, local browser checks and deployment/provider/evaluation adapter handoff.

No production database changes, live-provider claims, scheduler activation or paid infrastructure are authorized by this audit.
