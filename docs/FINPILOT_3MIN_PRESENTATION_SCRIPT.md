# FinPilot AI — 3-minute presentation script

Md. Meherab Hossain Talukder · Solo Participant

Timing guide: 15 + 40 + 45 + 45 + 35 seconds = 3:00. Rehearse with a timer; speaking speed varies.

## Slide 1 — 0:00–0:15

Hello, I am Meherab Hossain Talukder, a solo participant. FinPilot AI is a Financial Survival Copilot for freelancers and small business owners. It answers a practical question: can I spend today without risking my next essential payment?

## Slide 2 — 0:15–0:55

The problem is timing. A freelancer may expect enough income this month, yet a bill can be due before the client pays. Expected income is not available cash. Personal Mode separates received cash, expected payments, essential bills and an emergency reserve. Users see a conservative spending buffer, then compare choices before acting. An unexpected expense, delayed income, savings transfer or lower future income stays a simulation and never changes paid records. Personal and business workspaces remain separate, and the consumer experience works on phones as well as desktops.

## Slide 3 — 0:55–1:40

Here is the central example, using synthetic data. Our freelancer has eighteen thousand taka in paid cash, twelve thousand in upcoming essential bills, ten thousand expected from a client, and an eight-thousand-taka reserve target. If income arrives on time, ending cash is sixteen thousand. Now delay that payment by seven days. Ending cash is still sixteen thousand, but the lowest balance falls to six thousand before the payment arrives. That creates a two-thousand-taka reserve shortfall. This is not negative cash: it is a breach of the chosen reserve. A monthly total alone misses the risk.

## Slide 4 — 1:40–2:25

The architecture keeps calculations and explanations separate. Django and PostgreSQL hold authorized workspace records. A Decimal-based engine calculates dated cash positions and scenario differences. Groq explains the relevant evidence with references, assumptions and conditional trade-offs. Structured output is validated; an invalid or unavailable provider returns a clearly labeled calculated fallback. AI cannot execute payments or move money. The image is an actual saved Groq response from a synthetic private workspace. The account-free public demo is different: its explanations are deterministic. This separation makes the role of AI clear and keeps financial figures grounded in records.

## Slide 5 — 2:25–3:00

For this buildathon, I extended an existing SME application with dedicated Personal Mode, consumer onboarding, four personal scenarios and a public synthetic demo. Existing business tools were preserved. The documented PostgreSQL release passed three hundred sixty-eight tests, with browser checks across seven screen widths. Users can review records and export reports. The next steps are consent-based bank imports and richer personal budgeting. FinPilot helps people see timing risk and make a clearer decision before spending. You can try the account-free demo at this link. Thank you.
