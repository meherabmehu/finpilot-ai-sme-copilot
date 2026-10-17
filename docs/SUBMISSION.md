# Technical submission summary

FinPilot AI is a Python/Django modular monolith with server-rendered templates, locally compiled Tailwind, vanilla JavaScript, Chart.js, DRF and PostgreSQL production configuration. Its signature workflow is an account owning several independently authorized business workspaces.

Financial algorithms use Decimal: operating and cash reconciliation, moving-average baseline projections, weekly walk-forward evaluation, explicitly parameterized scenario deltas, and reducing-balance loan schedules. No trained model is required or downloaded.

The AI bridge uses a configurable compatible API, read-only tool allowlists, strict argument validation and server-bound business context. Authorization remains deterministic and independent of model behavior. The UI clearly separates actual records, estimates, simulations, synthetic demo data and unavailable AI.

See TESTING.md for actual verification evidence and LIMITATIONS.md for omitted functionality. This is an integrated MVP with explicit limitations, not an audited accounting system or autonomous payments platform.
