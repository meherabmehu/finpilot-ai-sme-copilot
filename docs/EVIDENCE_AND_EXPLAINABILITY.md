# Evidence and explainability

Each investigation saves an authorized business snapshot and fingerprint, cash calculation node, dated transaction/recurrence nodes, projection node, plan nodes and provenance edges. Detail exposes formulas/references and a collapsed deterministic tool trace. This is a lightweight JSON evidence graph, not a separate graph database or external citation system.

Labels distinguish recorded/calculated cash, estimated timelines, simulated plans, recommended-for-review alternatives and unknown outcomes. Saved policies and amounts are historical; later preference changes do not relabel prior results. Original transaction references are scoped through the investigation's business rather than arbitrary IDs supplied by a client.

Reports → Investigations & scenario evidence exports historical calculations, scenario metrics, constraints, dependencies, evidence nodes and outcomes. Decision history exports include the selected modified snapshot. CSV/XLSX cells use existing formula-injection escaping and PDF text is XML-escaped. Issue exports reflect latest persisted monitoring state (not a read-triggered refresh). Creation-date filters apply to investigation/decision exports, not the underlying evidence dates or current issues.

The snapshot fingerprint detects ordinary application changes; it is not a cryptographic attestation, immutable external ledger, source verification or independent accounting audit.

Final hardening: report_sections.py produces shared executive, financial-state, alternative, selected-plan, simulated-outcome, observed-outcome, assumptions and limitations sections. PDF uses paginated wrapped tables and an optional evidence appendix rather than raw dictionaries. XLSX keeps generated financial amounts numeric while escaping untrusted text. Overdue-recovery plans include their original invoice nodes, not invented customer citations.
