# Groq setup

Groq (`gsk_...`) and xAI Grok use separate credentials and endpoints. The same
server-owned evidence validation, bounded calls, and deterministic fallback apply
to either provider. No financial data is sent for out-of-scope questions.

Set these in your ignored local `.env`:

```dotenv
FINPILOT_AI_ENABLED=true
FINPILOT_AI_PROVIDER=groq
GROQ_API_KEY=your-private-key
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL=openai/gpt-oss-20b
```

Restart Django after changing environment variables. For Render, enter the same
variables under the web service's Environment settings and redeploy code containing
Groq support. A local `.env` change does not change the hosted environment.

Run `python manage.py check_ai_provider` for an offline configuration check.
`python manage.py check_ai_provider --live` checks whether the configured model is
listed for your key, without sending ledger data. A successful model-list check
does not verify inference or available quota. Never commit or paste the key.

`openai/gpt-oss-20b` is a Groq-hosted model supporting strict structured output;
this integration requires a model supporting `json_schema` with `strict: true`.
See [Groq structured outputs](https://console.groq.com/docs/structured-outputs)
and [API compatibility](https://console.groq.com/docs/openai).
