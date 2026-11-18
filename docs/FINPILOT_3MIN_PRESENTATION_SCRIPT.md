# FinPilot AI — 3-minute presentation script

Md. Meherab Hossain Talukder · Solo Participant

Exactly four slides, matching the original template. Solution-focused pitch with QR demo access.

Timing: 15 + 60 + 55 + 50 seconds = 3:00. Rehearse with a timer; speaking speed varies.

## Slide 1 — 0:00–0:15

Hello, I am Meherab Hossain Talukder, a solo participant. FinPilot AI is a Financial Survival Copilot for freelancers and small business owners. It helps answer one question: can I spend today without putting my next essential payment at risk?

## Slide 2 — 0:15–1:15

The problem is timing: an expected client payment may arrive after a bill is due. FinPilot makes that timing visible. Personal Mode starts with paid cash, expected income and its date, essential bills, and an emergency reserve. The dashboard separates money already received from promises of future income. A conservative spending buffer excludes future receipts. Next, the user can compare four decisions: delayed income, an unexpected expense, a proposed savings transfer, or reduced future income. Each comparison shows how the decision changes the cash position and reserve gap. Simulations never alter paid records. The private Advisor then explains relevant evidence and assumptions, while PDF, CSV and spreadsheet exports support review. Separate personal and business workspaces keep the context clear, and the same workflow works on mobile.

## Slide 3 — 1:15–2:10

Here is the solution in action, using synthetic data. Our freelancer has eighteen thousand taka in paid cash, twelve thousand in upcoming bills, ten thousand expected from a client, and an eight-thousand-taka reserve target. If the income arrives on time, ending cash is sixteen thousand. Now delay that receipt by seven days. Ending cash remains sixteen thousand, but the lowest balance falls to six thousand before the payment arrives. FinPilot reveals a two-thousand-taka reserve shortfall. This is not negative cash: it is a breach of the user’s chosen reserve. Cash after bills, excluding future receipts, is six thousand, so conservative spending room is zero. The practical benefit is seeing a risk that the monthly ending total hides, before making a spending decision.

## Slide 4 — 2:10–3:00

The system keeps financial calculations separate from AI explanations. Django and PostgreSQL manage authorized records, and a Decimal engine calculates amounts and dated scenarios. Groq explains the evidence with references and conditional reasoning. Structured output is validated; if the provider fails, the app returns a clearly labeled calculated explanation. AI cannot move money. The account-free public demo is deterministic, while private workspaces use the configured AI. For this buildathon, I extended an existing SME application with dedicated consumer onboarding, Personal Mode and four consumer scenarios. The documented release passed three hundred sixty-eight PostgreSQL tests, with browser checks at seven screen widths. Scan this QR code to try the synthetic demo without an account. FinPilot helps people make a clearer decision before spending. Thank you.
