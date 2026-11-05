You are a product demo filmmaker, screen-recording editor and AI voiceover producer.
Create the finished video described below, not just a script or a storyboard. This
prompt is self-contained; you have no earlier conversation to rely on.

# Objective

Produce a polished, truthful, approximately 2 minute 40 second English demo video
for **FinPilot AI – Financial Survival Copilot**, suitable for a hackathon submission
and later YouTube upload. Target 2:30–2:55; do not exceed 3:00. Use a natural AI
narrator, real product footage and the supplied actual application screenshots.

The primary audience is judges encountering the product for the first time. Show
the problem, working consumer workflow, timing-based scenario insight, meaningful
AI role and practical outcome. Prioritize a clear demonstration over promotional
claims. Create a finished MP4 if your environment supports video production. If it
does not, state that limitation honestly and deliver the usable components you can
actually create; do not invent a rendered download link.

# Product and participant context

- Product: FinPilot AI – Financial Survival Copilot.
- Creator: **Md. Meherab Hossain Talukder**.
- Participation: **Solo Participant**. Never imply a team of developers.
- Event: **Ostad presents YUNet AIgnite Buildathon 2026**.
- Audience: freelancers, students, individual sellers and small business owners.
- Purpose: help users understand paid cash, anticipate possible cash shortages,
  protect essential payments and compare financial decisions before acting.
- Positioning: financial decision support using recorded data and explicit
  assumptions. Projections are conditional estimates, not guaranteed predictions.
- The project existed as an SME application before this buildathon. Meaningful new
  work includes dedicated Personal Mode, consumer onboarding, conservative spending
  and savings calculations, four consumer scenarios, consumer-specific AI context
  and an account-free synthetic demo. Do not claim everything was built from zero
  during the event.

# Source links — use these actual resources

Primary live application:
https://finpilot-ai-web.onrender.com/

Account-free public demo — preferred for recording, no credentials required:
https://finpilot-ai-web.onrender.com/demo/personal/

Public demo PDF export:
https://finpilot-ai-web.onrender.com/demo/personal/?format=pdf

Alternative live application:
https://finpilot-ai-sme-copilot.vercel.app/

Alternative account-free demo:
https://finpilot-ai-sme-copilot.vercel.app/demo/personal/

GitHub repository:
https://github.com/meherabmehu/finpilot-ai-sme-copilot

Implementation branch:
https://github.com/meherabmehu/finpilot-ai-sme-copilot/tree/feat/finpilot-platform

Five-slide presentation PDF:
https://finpilot-ai-web.onrender.com/static/submission/finpilot-aignite-2026.pdf

PowerPoint version of the same five slides:
https://finpilot-ai-web.onrender.com/static/submission/finpilot-aignite-2026.pptx

Editable HTML presentation:
https://finpilot-ai-web.onrender.com/static/submission/finpilot-aignite-2026.html

Project image gallery ZIP — six numbered PNGs, all 1536×1024:
https://finpilot-ai-web.onrender.com/static/submission/finpilot-devpost-gallery.zip

Judge package — presentation, project story and product brief:
https://finpilot-ai-web.onrender.com/static/submission/finpilot-submission-package.zip

Thumbnail — PNG, 1536×1024, exact 3:2, approximately 1.68 MB:
https://finpilot-ai-web.onrender.com/static/submission/finpilot-thumbnail.png

Original official event sticker — preserve unmodified:
https://finpilot-ai-web.onrender.com/static/buildathon/yunet-aignite-buildathon-2026-sticker.jpeg

Actual Personal dashboard screenshot:
https://finpilot-ai-web.onrender.com/static/submission/images/personal-dashboard.png

Actual scenario comparison screenshot:
https://finpilot-ai-web.onrender.com/static/submission/images/personal-scenario.png

Actual full Advisor screenshot:
https://finpilot-ai-web.onrender.com/static/submission/images/personal-advisor.png

Enlarged actual saved Groq response excerpt — use this for readable AI footage:
https://finpilot-ai-web.onrender.com/static/submission/images/personal-advisor-excerpt.png

Individual gallery images:
https://finpilot-ai-web.onrender.com/static/submission/devpost-gallery/01-finpilot-cover.png
https://finpilot-ai-web.onrender.com/static/submission/devpost-gallery/02-personal-dashboard.png
https://finpilot-ai-web.onrender.com/static/submission/devpost-gallery/03-payment-delay-scenario.png
https://finpilot-ai-web.onrender.com/static/submission/devpost-gallery/04-explainable-ai-advisor.png
https://finpilot-ai-web.onrender.com/static/submission/devpost-gallery/05-small-business-dashboard.png
https://finpilot-ai-web.onrender.com/static/submission/devpost-gallery/06-mobile-personal-mode.png

Public Devpost project URL, if accessible; publication status is not assumed:
https://devpost.com/software/finpilot-ai-financial-survival-copilot

If a Render page is slow on first access, allow it time to start, then retry. Use
the Vercel alternative if necessary. If the origin is unavailable, use the supplied
screenshots and identify them as saved captures. Do not fabricate a live session.

# What is actually implemented

1. **Personal onboarding:** available cash, income type, expected income and date,
   recurring essential bills, emergency reserve, optional savings target and record
   completeness. Personal and Business workspaces are distinct.
2. **Personal dashboard:** paid cash, upcoming bills, cash after bills excluding
   future receipts, reserve target, conservative spending/savings room and dated
   planning context. Missing records can make estimates incomplete.
3. **Four personal scenario types:** delay selected expected income by 7/14/30 days;
   add an unexpected expense; model a proposed savings transfer; reduce future
   income by 10/20/30 percent. Dates and assumptions matter. Comparisons do not
   alter paid records; saved scenarios remain hypothetical.
4. **Private AI Advisor:** authorized workspace evidence is calculated using a
   deterministic financial engine. Groq helps explain evidence and conditional
   trade-offs. Evidence references and structured output are validated. Provider
   failure leads to a truthfully labeled calculated fallback. AI cannot move money,
   execute payments, approve credit or freely invent financial amounts.
5. **Existing Business Mode:** cash planning, essential payment priorities, overdue
   collections, decision/scenario tools and financial reporting remain available.
6. **Exports:** PDF, CSV and XLSX in private workflows; the public synthetic demo
   offers a genuine PDF snapshot.
7. **Responsive application:** phone, tablet and desktop layouts. Browser checks
   covered 320, 375, 390, 768, 1024, 1440 and 1920 pixel widths.
8. **Stack:** Python, Django, PostgreSQL, Decimal arithmetic, Pydantic, Django
   templates, Tailwind CSS, JavaScript, Chart.js and Groq. Hosted on Render/Vercel.
9. **Measured validation:** 368 PostgreSQL tests passed at the documented release;
   actual Groq execution was verified in an isolated synthetic Personal workspace.
   This is testing evidence, not evidence of commercial adoption or forecast accuracy.

# Central demonstration — preserve these exact synthetic figures

The public demo models:

| Measure | Amount |
|---|---:|
| Cash actually available | BDT 18,000 |
| Upcoming essential bills | BDT 12,000 |
| Expected client income | BDT 10,000 |
| Emergency reserve target | BDT 8,000 |
| Cash after bills, excluding future income | BDT 6,000 |
| Conservative spending room | BDT 0 |

Baseline: expected income arrives before the essential bill, ending cash is
BDT 16,000 and there is no reserve shortfall in this synthetic example.

Seven-day delay: ending cash remains BDT 16,000, but the lowest interim balance
falls to BDT 6,000. Against the BDT 8,000 reserve target, this produces a BDT 2,000
reserve shortfall. The insight is: **same ending balance, different interim risk**.
This is a reserve shortfall, not a claim that cash becomes negative.

Use the actual app's current relative dates; do not invent dates or make old saved
capture dates look like current live data. Do not replace “expected” with “received.”

# Essential truthfulness and access rules

- **Public demo:** account-free, stateless, synthetic and deterministic. Never
  present its explanatory output as a live Groq response.
- **Private Advisor:** genuine Groq integration exists. Use the supplied actual
  saved synthetic response capture unless authorized synthetic credentials are
  separately available. No credentials are included in this prompt. Do not create
  accounts or bypass login to obtain private footage.
- Label the private Advisor sequence **“Saved Groq response · synthetic workspace”**
  when using the supplied screenshot. An animated cursor must not imply a new AI
  answer was generated during the recording.
- Reframing or enlarging actual screenshots for readability is allowed. Generating
  fake application UI, changing figures, inventing chat replies, fabricating bank
  connections, users, testimonials, revenue or awards is not.
- Bank synchronization, calibrated predictive models, automatic notifications and
  autonomous financial actions are not implemented features to advertise.
- Never record passwords, `.env` files, API keys, private account details or real
  customer financial data. Use marked synthetic footage only.
- Do not publish to YouTube, submit to Devpost or send messages. Deliver the video
  files to me; external publishing is a separate action.

# Visual direction

- 16:9, 1920×1080, 30 fps, clean screen-recorded product film.
- Match the product: midnight navy, teal/mint, white and soft pale backgrounds.
- Keep actual interface text readable: deliberate zooms, focused crops, cursor
  highlights and a pause after a result appears. Avoid entire dashboards shrunk
  into tiny picture-in-picture windows.
- The supplied AI response excerpt should occupy most of its scene. Never use the
  tiny full-page Advisor image as the only demonstration of AI.
- Use restrained transitions and simple motion to explain timing. No stock money
  rain, exaggerated profits, fake dashboards or distracting avatar covering the app.
- Opening/closing credit: “Md. Meherab Hossain Talukder · Solo Participant.”
- Display the original event sticker briefly, at its original aspect ratio, without
  cropping, redrawing, removing sponsors or making its text unreadable.
- The 3:2 thumbnail is marketing artwork, not an app screenshot. Letterbox it or
  use it as a supporting cover element; do not stretch it to fill 16:9.
- The original presentation remains five slides; the video may use multiple scenes
  without adding slides to the submitted presentation.

# Voice and sound

Use a natural, calm, confident English AI narrator with clear international
pronunciation, approximately 135–145 words per minute. Avoid robotic delivery and
exaggerated sales language. This is an AI presenter, not a clone or impersonation
of the founder. Do not claim the synthetic voice is the founder's real voice.

Pronunciations: “FinPilot” = “Fin Pilot”; Groq = “grock”; BDT = “Bangladeshi taka.”
Say amounts naturally, for example “eighteen thousand taka.”

Use clean narration with optional very quiet instrumental background music. Music
must not compete with speech. Keep narration around -16 LUFS integrated, peaks
below -1 dBTP, and background music approximately 18–24 dB below speech. Add accurate
English subtitles with safe margins and sufficient contrast. Do not cover key UI
figures, buttons or result rows with captions.

# Scene plan and final narration

Keep the following narrative truthful. Minor timing or wording adjustments for
natural speech are allowed, but preserve every distinction about synthetic data,
public deterministic explanations and private AI.

## 0:00–0:20 — The problem

Visual: a short FinPilot title card with participant credit, then a simple animated
payment-date versus bill-date illustration. Identify this animation as explanatory,
not an application screen. Show the actual official sticker briefly.

Voiceover:
“A client payment is on its way. Your essential bill is due tomorrow. Can you spend
today without putting your emergency reserve at risk? For freelancers and small
business owners, monthly totals can miss the problem. Expected income is not
available cash.”

## 0:20–0:40 — Introduce the working product

Visual: open the actual live landing page and enter the account-free Personal demo.
Show “Synthetic demo” clearly. Avoid spending the video on login forms.

Voiceover:
“Meet FinPilot AI, a Financial Survival Copilot. Created by solo participant
Md. Meherab Hossain Talukder, it extends an existing business application with
dedicated Personal Mode. Personal records and business workspaces stay separate.
This public demo uses synthetic data and needs no account.”

## 0:40–1:05 — Cash versus expected income

Visual: zoom the actual demo cards, highlighting 18,000 paid cash, 12,000 bills,
10,000 expected income and 8,000 reserve. Then highlight 6,000 cash after bills and
zero conservative spending room. Do not obscure labels.

Voiceover:
“Our synthetic freelancer has eighteen thousand taka available, twelve thousand in
upcoming bills, ten thousand expected from a client, and an eight-thousand-taka
reserve target. Excluding future receipts, cash after bills is only six thousand.
Conservative spending room is zero. An unpaid promise does not become spending
money.”

## 1:05–1:35 — Demonstrate the seven-day delay

Visual: in the actual public demo, select the income-delay scenario, seven days and
the available synthetic income. Click the real comparison button. Hold on the
baseline/simulated result. Highlight ending cash, lowest cash and reserve shortfall.
Use a simple timing annotation if helpful, without altering the screenshot.

Voiceover:
“Now delay the selected income by seven days. Ending cash is still sixteen
thousand, but the lowest balance falls to six thousand before the delayed payment
arrives. That creates a two-thousand-taka reserve shortfall. The same ending balance
can hide a very different week. Users can also compare unexpected expenses,
savings transfers and reduced future income. Simulations never change actual cash.”

## 1:35–2:05 — Explain the real AI role

Visual: transition explicitly to the enlarged saved private Groq response excerpt.
Display “Saved Groq response · synthetic workspace.” Highlight its conditional
wording and evidence references. Briefly show the flow “Records → calculations →
Groq explanation → user decision” using clear native text.

Voiceover:
“This saved response comes from the real Groq Advisor in an isolated synthetic
private workspace. The financial engine calculates the figures; Groq explains
relevant evidence and conditional trade-offs. AI cannot execute payments or freely
invent amounts. Provider failures use a clearly labeled calculated fallback.
The account-free public demo's explanations are deterministic, not live AI.”

## 2:05–2:25 — Practical use and engineering

Visual: use the supplied mobile and Business screenshots with appropriate synthetic
labels; show the public demo's genuine PDF export. Keep these views large enough
to read. A short badge may say “368 PostgreSQL tests passed” without implying
financial forecasts are guaranteed accurate.

Voiceover:
“Users can review essential bills, correct their records and download financial
reports. The interface supports phones, tablets and desktops while preserving the
existing business tools. The PostgreSQL suite passed three hundred sixty-eight
tests, with browser checks across seven screen widths.”

## 2:25–2:40 — Close with a clear call to action

Visual: clean closing card with product name, creator name, “Solo Participant” and
the exact public demo URL. Optional QR code must encode that real URL. Hold the
URL for at least five seconds. Add a small line: “Decision support; estimates
depend on recorded data and assumptions.”

Voiceover:
“FinPilot helps people make a clearer decision before spending. It combines
personal financial context, transparent calculations, scenario planning and
grounded AI. Try the account-free synthetic demo using the link on screen.”

Closing link:
https://finpilot-ai-web.onrender.com/demo/personal/

# Deliverables

1. `FinPilot_AI_Demo_1080p.mp4` — finished H.264 MP4, 1080p/30 fps, AAC audio.
2. `FinPilot_AI_Voiceover.wav` or `.mp3` — final clean AI narration.
3. `FinPilot_AI_English.srt` — accurate timed captions, also burned into a captioned
   MP4 version if possible.
4. `FinPilot_AI_Final_Script.txt` — narration actually used, plus scene timestamps.
5. Preserve the supplied original thumbnail and offer a separate 16:9 YouTube cover
   only if needed; do not replace the original 3:2 Devpost thumbnail.
6. The editable video project/timeline, if supported by your platform.

Before delivery, watch the complete render. Confirm correct spelling of the creator
name, readable UI, legible captions, correct BDT amounts, no stretched assets,
working audio, duration under three minutes and a playable final MP4. Check that
the public deterministic demo and saved private AI response are clearly distinct.
If anything could not be recorded or generated, list that specific limitation.

Start by downloading and inspecting the supplied assets, then record, narrate,
edit and render the video. Do not stop after giving another production plan.
