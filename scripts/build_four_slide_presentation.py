"""Use exactly the four supplied template slides; solution-led pitch and verified QR."""
from pathlib import Path

from PIL import Image, ImageDraw
from pptx import Presentation
from pptx.util import Inches
from reportlab.graphics.barcode.qr import QrCodeWidget

from scripts.build_template_presentation import GRAY, NAVY, ORANGE, TEAL, box, text

DEMO = 'https://finpilot-ai-web.onrender.com/demo/personal/'
NOTES = [
    (15, 'Hello, I am Meherab Hossain Talukder, a solo participant. FinPilot AI is a Financial Survival Copilot for freelancers and small business owners. It helps answer one question: can I spend today without putting my next essential payment at risk?'),
    (60, 'The problem is timing: an expected client payment may arrive after a bill is due. FinPilot makes that timing visible. Personal Mode starts with paid cash, expected income and its date, essential bills, and an emergency reserve. The dashboard separates money already received from promises of future income. A conservative spending buffer excludes future receipts. Next, the user can compare four decisions: delayed income, an unexpected expense, a proposed savings transfer, or reduced future income. Each comparison shows how the decision changes the cash position and reserve gap. Simulations never alter paid records. The private Advisor then explains relevant evidence and assumptions, while PDF, CSV and spreadsheet exports support review. Separate personal and business workspaces keep the context clear, and the same workflow works on mobile.'),
    (55, 'Here is the solution in action, using synthetic data. Our freelancer has eighteen thousand taka in paid cash, twelve thousand in upcoming bills, ten thousand expected from a client, and an eight-thousand-taka reserve target. If the income arrives on time, ending cash is sixteen thousand. Now delay that receipt by seven days. Ending cash remains sixteen thousand, but the lowest balance falls to six thousand before the payment arrives. FinPilot reveals a two-thousand-taka reserve shortfall. This is not negative cash: it is a breach of the user’s chosen reserve. Cash after bills, excluding future receipts, is six thousand, so conservative spending room is zero. The practical benefit is seeing a risk that the monthly ending total hides, before making a spending decision.'),
    (50, 'The system keeps financial calculations separate from AI explanations. Django and PostgreSQL manage authorized records, and a Decimal engine calculates amounts and dated scenarios. Groq explains the evidence with references and conditional reasoning. Structured output is validated; if the provider fails, the app returns a clearly labeled calculated explanation. AI cannot move money. The account-free public demo is deterministic, while private workspaces use the configured AI. For this buildathon, I extended an existing SME application with dedicated consumer onboarding, Personal Mode and four consumer scenarios. The documented release passed three hundred sixty-eight PostgreSQL tests, with browser checks at seven screen widths. Scan this QR code to try the synthetic demo without an account. FinPilot helps people make a clearer decision before spending. Thank you.'),
]


def header(slide, title, subtitle, number):
    text(slide, .48, .88, 9.04, .53, title, 25, bold=True)
    text(slide, .5, 1.44, 9, .44, subtitle, 12, GRAY)
    text(slide, .5, 5.02, 8.6, .2, 'FinPilot AI  |  Md. Meherab Hossain Talukder  |  Solo Participant', 8, GRAY)
    text(slide, 9, 5.02, .5, .2, f'{number}/4', 9, GRAY)


def make_qr(path):
    qr = QrCodeWidget(DEMO).qr
    qr.make()
    quiet, cell = 4, 18
    side = (len(qr.modules)+quiet*2)*cell
    image = Image.new('RGB', (side, side), 'white')
    draw = ImageDraw.Draw(image)
    for y, row in enumerate(qr.modules):
        for x, dark in enumerate(row):
            if dark:
                left, top = (x+quiet)*cell, (y+quiet)*cell
                draw.rectangle((left, top, left+cell-1, top+cell-1), fill='black')
    image.save(path)
    import zxingcpp
    decoded = zxingcpp.read_barcode(image)
    assert decoded is not None and decoded.text == DEMO
    print('QR independently decoded to the exact public demo URL.')


def main():
    presentation = Presentation('C:/Users/USER/Downloads/YUnet_AIgnite_Project_presentation_Template.pptx')
    template_count = len(presentation.slides)
    assert template_count == 4
    cover = presentation.slides[0]
    text(cover, 2.88, 3.88, 5.38, .28, 'FinPilot AI – Financial Survival Copilot', 16, bold=True)
    text(cover, 3.69, 4.31, 3.5, .2, 'Md. Meherab Hossain Talukder', 12, bold=True)
    text(cover, 3.69, 4.59, 4.2, .23, 'Solo Participant', 10, GRAY)
    slide = presentation.slides[1]
    header(slide, 'A clear solution before every money decision.', 'For freelancers and small businesses: see timing risk before an essential bill is due.', 2)
    steps = [(2.02, '01  KNOW YOUR CASH', 'Paid cash, expected income, bills and reserve.'),
             (2.69, '02  COMPARE YOUR OPTIONS', 'Income delay · expense · savings · lower income.'),
             (3.36, '03  UNDERSTAND THE EVIDENCE', 'Private AI guidance, assumptions and report exports.')]
    for y, title, detail in steps:
        box(slide, .5, y, 4.6, .59, 'F4F0FA')
        text(slide, .65, y+.07, 4.3, .23, title, 12, TEAL, True)
        text(slide, .65, y+.32, 4.3, .2, detail, 10, GRAY)
    source = Path('static/submission/images/personal-dashboard.png')
    with Image.open(source) as image:
        crop_bottom = max(0, 1-(image.width/(4.1/1.98))/image.height)
    picture = slide.shapes.add_picture(str(source), Inches(5.35), Inches(2.04), width=Inches(4.1), height=Inches(1.98))
    picture.crop_bottom = crop_bottom
    text(slide, 5.38, 4.12, 4.02, .2, 'Actual Personal Mode · synthetic records', 9, GRAY)
    box(slide, .5, 4.42, 9, .4, 'FFF2EA')
    text(slide, .66, 4.51, 8.67, .23, 'Personal + Business workspaces  •  Mobile-ready  •  Simulations never change paid cash', 12, bold=True)
    slide = presentation.slides[2]
    header(slide, 'See the shortage a monthly total can hide.', 'Solution in action · synthetic BDT example · one expected receipt delayed by seven days.', 3)
    for x, amount, label in [(.5,'18,000','Paid cash'), (2.8,'12,000','Essential bills'), (5.1,'10,000','Expected income'), (7.4,'8,000','Reserve target')]:
        box(slide, x, 1.97, 2.1, .85, 'F4F0FA')
        text(slide, x+.12, 2.03, 1.86, .43, amount, 22, bold=True)
        text(slide, x+.12, 2.46, 1.86, .21, label, 10, GRAY)
    rows = [('Measure','On time','7 days late'), ('Ending cash','16,000','16,000'), ('Lowest cash','16,000','6,000'), ('Reserve shortfall','0','2,000')]
    for i, row in enumerate(rows):
        y = 2.96+i*.36
        if i in (0,3):
            box(slide, .5, y, 9, .34, 'FFF1E8' if i == 3 else 'EEF4F5')
        for x, w, value in zip([.68,4.55,7], [3.65,2,2.1], row, strict=True):
            text(slide, x, y+.045, w, .28, value, 14, ORANGE if i == 3 else NAVY, i in (0,3))
    text(slide, .6, 4.49, 8.9, .24, 'Same ending balance. A BDT 2,000 interim reserve gap.', 15, TEAL, True)
    text(slide, .6, 4.79, 8.9, .18, 'Cash after bills: 6,000 · Conservative spending room: 0 · Reserve gap is not negative cash.', 9, GRAY)
    slide = presentation.slides[3]
    header(slide, 'Calculated facts. Explainable AI. Your decision.', 'Python / Django / PostgreSQL · Decimal arithmetic · Groq · responsive web interface', 4)
    steps = [(1.98, '1  CALCULATE', 'Authorized records → dated cash and scenario results.'),
             (2.62, '2  EXPLAIN', 'Groq adds evidence-linked guidance; validated fallback.'),
             (3.26, '3  KEEP CONTROL', 'AI cannot move money. Personal and business stay separate.')]
    for y, title, detail in steps:
        box(slide, .5, y, 5.85, .56, 'F4F0FA')
        text(slide, .65, y+.055, 5.55, .24, title, 13, TEAL, True)
        text(slide, .65, y+.31, 5.55, .19, detail, 10, GRAY)
    text(slide, .55, 4.03, 5.8, .31, '368 PostgreSQL tests passed · 7 screen widths', 14, bold=True)
    text(slide, .55, 4.48, 5.8, .44, 'Buildathon addition: Personal Mode + four consumer scenarios.\nExisting SME tools preserved; reports export to PDF / CSV / XLSX.', 10, GRAY)
    qr_path = Path('static/submission/finpilot-demo-qr.png')
    make_qr(qr_path)
    box(slide, 6.65, 1.95, 2.85, 2.95, 'F0F7F4')
    text(slide, 6.87, 2.08, 2.42, .3, 'SCAN THE LIVE DEMO', 13, TEAL, True)
    slide.shapes.add_picture(str(qr_path), Inches(7.02), Inches(2.48), width=Inches(2.1))
    text(slide, 6.87, 4.63, 2.42, .18, 'No account · synthetic data', 9, GRAY)
    notes = ['# FinPilot AI — 3-minute presentation script', '', 'Md. Meherab Hossain Talukder · Solo Participant', '', 'Exactly four slides, matching the original template. Solution-focused pitch with QR demo access.', '', 'Timing: 15 + 60 + 55 + 50 seconds = 3:00. Rehearse with a timer; speaking speed varies.', '']
    elapsed = 0
    for i, (slide, (duration, script)) in enumerate(zip(presentation.slides, NOTES, strict=True), 1):
        start = f'{elapsed//60}:{elapsed%60:02}'
        end = f'{(elapsed+duration)//60}:{(elapsed+duration)%60:02}'
        slide.notes_slide.notes_text_frame.text = f'SLIDE {i} | {start}–{end} | {duration} seconds\n\n{script}'
        notes.extend([f'## Slide {i} — {start}–{end}', '', script, ''])
        elapsed += duration
    presentation.core_properties.author = 'Md. Meherab Hossain Talukder'
    presentation.core_properties.title = 'FinPilot AI — Four-slide solution pitch'
    destination = Path('static/submission/FinPilot_AI_Official_Template_3min.pptx')
    presentation.save(destination)
    Path('docs/FINPILOT_3MIN_PRESENTATION_SCRIPT.md').write_text('\n'.join(notes), encoding='utf-8')
    check = Presentation(destination)
    assert len(check.slides) == template_count
    for slide in check.slides:
        assert slide.notes_slide.notes_text_frame.text
        for shape in slide.shapes:
            assert 0 <= shape.left and shape.left+shape.width <= check.slide_width
            assert 0 <= shape.top and shape.top+shape.height <= check.slide_height
            if shape.has_text_frame:
                assert 'https://' not in shape.text and 'Try:' not in shape.text
    print(f'Exactly {template_count} slides; {sum(len(s.split()) for _, s in NOTES)} words; 180-second timing guide.')


if __name__ == '__main__':
    main()
