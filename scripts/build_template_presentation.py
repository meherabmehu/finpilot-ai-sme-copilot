"""Create an editable three-minute pitch in the supplied official PowerPoint template."""
import argparse
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt

NAVY = '21164C'
ORANGE = 'FB6535'
TEAL = '087F73'
GRAY = '526174'


def box(slide, x, y, w, h, fill, line=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor.from_string(fill)
    shape.line.fill.background() if line is None else None
    if line:
        shape.line.color.rgb = RGBColor.from_string(line)
    return shape


def text(slide, x, y, w, h, value, size=16, color=NAVY, bold=False):
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = shape.text_frame
    frame.word_wrap = True
    frame.margin_left = frame.margin_right = Inches(.02)
    frame.margin_top = frame.margin_bottom = 0
    for index, line in enumerate(value.split('\n')):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.text = line
        paragraph.font.name = 'Arial'
        paragraph.font.size = Pt(size)
        paragraph.font.bold = bold
        paragraph.font.color.rgb = RGBColor.from_string(color)
        paragraph.space_after = Pt(3)
    return shape


def header(slide, title, subtitle, number):
    text(slide, .48, .88, 9.04, .53, title, 25, bold=True)
    text(slide, .5, 1.44, 9, .44, subtitle, 12, GRAY)
    text(slide, .5, 5.02, 8.6, .2, 'FinPilot AI  |  Md. Meherab Hossain Talukder  |  Solo Participant', 8, GRAY)
    text(slide, 9, 5.02, .5, .2, f'{number}/5', 9, GRAY)


NOTES = [
    (15, 'Hello, I am Meherab Hossain Talukder, a solo participant. FinPilot AI is a Financial Survival Copilot for freelancers and small business owners. It answers a practical question: can I spend today without risking my next essential payment?'),
    (40, 'The problem is timing. A freelancer may expect enough income this month, yet a bill can be due before the client pays. Expected income is not available cash. Personal Mode separates received cash, expected payments, essential bills and an emergency reserve. Users see a conservative spending buffer, then compare choices before acting. An unexpected expense, delayed income, savings transfer or lower future income stays a simulation and never changes paid records. Personal and business workspaces remain separate, and the consumer experience works on phones as well as desktops.'),
    (45, 'Here is the central example, using synthetic data. Our freelancer has eighteen thousand taka in paid cash, twelve thousand in upcoming essential bills, ten thousand expected from a client, and an eight-thousand-taka reserve target. If income arrives on time, ending cash is sixteen thousand. Now delay that payment by seven days. Ending cash is still sixteen thousand, but the lowest balance falls to six thousand before the payment arrives. That creates a two-thousand-taka reserve shortfall. This is not negative cash: it is a breach of the chosen reserve. A monthly total alone misses the risk.'),
    (45, 'The architecture keeps calculations and explanations separate. Django and PostgreSQL hold authorized workspace records. A Decimal-based engine calculates dated cash positions and scenario differences. Groq explains the relevant evidence with references, assumptions and conditional trade-offs. Structured output is validated; an invalid or unavailable provider returns a clearly labeled calculated fallback. AI cannot execute payments or move money. The image is an actual saved Groq response from a synthetic private workspace. The account-free public demo is different: its explanations are deterministic. This separation makes the role of AI clear and keeps financial figures grounded in records.'),
    (35, 'For this buildathon, I extended an existing SME application with dedicated Personal Mode, consumer onboarding, four personal scenarios and a public synthetic demo. Existing business tools were preserved. The documented PostgreSQL release passed three hundred sixty-eight tests, with browser checks across seven screen widths. Users can review records and export reports. The next steps are consent-based bank imports and richer personal budgeting. FinPilot helps people see timing risk and make a clearer decision before spending. You can try the account-free demo at this link. Thank you.'),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--template', default='C:/Users/USER/Downloads/YUnet_AIgnite_Project_presentation_Template.pptx')
    args = parser.parse_args()
    template = Path(args.template)
    presentation = Presentation(template)
    assert len(presentation.slides) == 4
    presentation.slides.add_slide(presentation.slides[1].slide_layout)
    # Blank inherited content placeholders on the newly added slide.
    for shape in list(presentation.slides[4].shapes):
        shape._element.getparent().remove(shape._element)
    cover = presentation.slides[0]
    text(cover, 2.88, 3.88, 5.38, .28, 'FinPilot AI – Financial Survival Copilot', 16, bold=True)
    text(cover, 3.69, 4.31, 3.5, .2, 'Md. Meherab Hossain Talukder', 12, bold=True)
    text(cover, 3.69, 4.59, 4.2, .23, 'Solo Participant', 10, GRAY)

    slide = presentation.slides[1]
    header(slide, 'A payment promise cannot pay today’s bill.', 'The problem: monthly totals hide the gap between income dates and bill deadlines.', 2)
    box(slide, .5, 2, 4.2, 2.64, 'FFF2EA')
    text(slide, .7, 2.18, 3.8, .35, 'FOR FREELANCERS & INDIVIDUAL SELLERS', 11, ORANGE, True)
    text(slide, .7, 2.7, 3.8, 1.5, '“Can I spend now and still\nprotect my next bill and\nemergency reserve?”', 21, bold=True)
    text(slide, 5, 2.05, 4.45, .36, 'A clear plan before a decision', 19, bold=True)
    for y, label in [(2.68, '01  Separate paid cash from expected income'), (3.24, '02  Protect essential bills and your reserve'), (3.8, '03  Compare scenarios without changing records')]:
        text(slide, 5, y, 4.43, .47, label, 14)
    text(slide, 5, 4.45, 4.43, .26, 'Personal Mode + separate Business workspaces', 11, TEAL, True)

    slide = presentation.slides[2]
    header(slide, 'Same ending balance. A very different week.', 'Synthetic example · BDT · delay one expected receipt by seven days.', 3)
    for x, amount, label in [(.5,'18,000','Paid cash'), (2.8,'12,000','Essential bills'), (5.1,'10,000','Expected income'), (7.4,'8,000','Reserve target')]:
        box(slide, x, 1.97, 2.1, .89, 'F4F0FA')
        text(slide, x+.12, 2.06, 1.86, .43, amount, 22, bold=True)
        text(slide, x+.12, 2.5, 1.86, .21, label, 10, GRAY)
    rows = [('Measure','On time','7 days late'), ('Ending cash','16,000','16,000'), ('Lowest cash','16,000','6,000'), ('Reserve shortfall','0','2,000')]
    for i, row in enumerate(rows):
        y = 3.03 + i*.38
        if i in (0,3):
            box(slide, .5, y, 9, .36, 'FFF1E8' if i == 3 else 'EEF4F5')
        for x,w,value in zip([.68,4.55,7],[3.65,2,2.1], row, strict=True):
            text(slide, x, y+.055, w, .27, value, 14, ORANGE if i == 3 else NAVY, i in (0,3))
    text(slide, .6, 4.66, 8.9, .25, 'A reserve shortfall, not negative cash. Future income is never guaranteed.', 11, TEAL, True)

    slide = presentation.slides[3]
    header(slide, 'Transparent calculations. Grounded AI guidance.', 'Records → Decimal engine → Groq explanation → user decision', 4)
    text(slide, .52, 2, 3.1, .4, 'How it works', 20, bold=True)
    text(slide, .52, 2.58, 3.15, 1.86, '• Authorized workspace records\n• Calculated amounts and dates\n• Evidence-linked explanations\n• Validated output + fallback', 15)
    text(slide, .52, 4.55, 3.15, .3, 'AI cannot move money.', 14, ORANGE, True)
    picture = Path('static/submission/images/personal-advisor-excerpt.png')
    slide.shapes.add_picture(str(picture), Inches(4.25), Inches(1.98), width=Inches(4.9))
    text(slide, 3.94, 4.6, 5.4, .39, 'Actual saved Groq response · synthetic workspace\nPublic demo explanations are deterministic.', 9, GRAY)

    slide = presentation.slides[4]
    header(slide, 'Built to help people decide before spending.', 'A working consumer extension, with existing small-business tools preserved.', 5)
    text(slide, .52, 2, 4.75, .4, 'Buildathon work', 20, bold=True)
    text(slide, .52, 2.55, 4.75, 1.7, '• Dedicated Personal onboarding\n• Four consumer what-if scenarios\n• Private AI + report exports\n• Account-free synthetic demo', 16)
    box(slide, 5.65, 2, 3.8, 1.48, 'F0F7F4')
    text(slide, 5.86, 2.18, 3.4, .4, '368 tests passed', 23, TEAL, True)
    text(slide, 5.86, 2.78, 3.4, .42, 'Documented PostgreSQL release\nBrowser checks at 7 screen widths', 11, GRAY)
    text(slide, 5.68, 3.76, 3.75, .63, 'Next: consent-based bank imports\nand richer personal budgeting.', 13)
    text(slide, .54, 4.52, 8.95, .28, 'Try: finpilot-ai-web.onrender.com/demo/personal/', 16, TEAL, True)
    link = slide.shapes[-1].text_frame.paragraphs[0].runs[0]
    link.hyperlink.address = 'https://finpilot-ai-web.onrender.com/demo/personal/'
    notes_document = ['# FinPilot AI — 3-minute presentation script', '', 'Md. Meherab Hossain Talukder · Solo Participant', '', 'Timing guide: 15 + 40 + 45 + 45 + 35 seconds = 3:00. Rehearse with a timer; speaking speed varies.', '']
    elapsed = 0
    for i, (slide, (duration, script)) in enumerate(zip(presentation.slides, NOTES, strict=True), 1):
        start, end = f'{elapsed//60}:{elapsed%60:02}', f'{(elapsed+duration)//60}:{(elapsed+duration)%60:02}'
        note = f'SLIDE {i} | {start}–{end} | {duration} seconds\n\n{script}'
        slide.notes_slide.notes_text_frame.text = note
        notes_document.extend([f'## Slide {i} — {start}–{end}', '', script, ''])
        elapsed += duration
    presentation.core_properties.author = 'Md. Meherab Hossain Talukder'
    presentation.core_properties.title = 'FinPilot AI — Financial Survival Copilot | 3-minute pitch'
    output = Path('static/submission/FinPilot_AI_Official_Template_3min.pptx')
    presentation.save(output)
    Path('docs/FINPILOT_3MIN_PRESENTATION_SCRIPT.md').write_text('\n'.join(notes_document), encoding='utf-8')
    check = Presentation(output)
    assert len(check.slides) == 5
    for slide in check.slides:
        assert slide.notes_slide.notes_text_frame.text
        for shape in slide.shapes:
            assert shape.left >= 0 and shape.top >= 0
            assert shape.left + shape.width <= check.slide_width
            assert shape.top + shape.height <= check.slide_height
    words = sum(len(script.split()) for _, script in NOTES)
    print(f'{output}: 5 slides, native editable text, original template retained; {words} spoken words, 180-second timing guide.')


if __name__ == '__main__':
    main()
