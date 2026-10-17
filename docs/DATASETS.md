# Data provenance

No ML model is trained, fine-tuned or downloaded. The seed command creates deterministic synthetic transactions for three fictional companies: electronics retail, restaurant, and fashion retail. Restaurant weekends have different sales; business scales, rent, payroll, supplies and obligations differ. All amounts reconcile through the same engine used by real accounts. No new real account is silently populated.

Online Retail II, M5, Olist, World Bank Enterprise Surveys, SBA lending and Polish bankruptcy datasets are potential research sources, not integrated training data or verified SME underwriting signals. They are not downloaded or redistributed. Respect each source's license and do not blindly merge differing populations, currencies or accounting definitions.

The generic CSV/XLSX adapter accepts normalized records. Specialized public-dataset adapters are not included. When adapting invoice-only retail datasets, use pending receivables rather than inventing confirmed payment dates, expenses or cash balances.
