# Agent tools and no-provider behavior

`advisor.run_tool` reauthorizes server-side business context for every allowlisted call. Pydantic schemas reject extra properties; callers cannot select another tenant, send SQL or execute code. Tools provide summaries, state, issue diagnosis, counterfactual comparison and recent business decision memory. The existing OpenAI-compatible adapter is preserved, with bounded rounds, eight tool calls, repetition rejection, checked runtime budget and safe tool errors. Tool budgets are not an operating-system hard cancellation deadline.

LLM arithmetic is not authoritative: financial facts must derive from deterministic tools. Configured provider explanations still require human review and can be wrong. Up to eight recent business-and-user-scoped messages provide bounded conversation context. Internal tools remain read-only; saved investigations require an explicit owner POST form.

With no API key/model, chat returns labeled deterministic cash, timeline, simulated alternatives, dependencies and missing information. This is not fabricated generative output. The Advisor page offers the same saved investigation entry as Planning. Internal deterministic traces are collapsed on investigation detail.

Live provider execution was not verified during this continuation. No credentials are shipped. Financial metadata sent to a configured provider requires the operator's privacy controls and user authority.

See AI_PROVIDER_READINESS.md for exact environment names, provider compatibility, runtime/token budgets, synthetic mocked integration tests and cost/privacy controls. Current no-provider explanations are intent-specific (collections, expenses, liquidity) and configured-provider tools honor explicit no-borrowing constraints. No live provider connection is claimed.
