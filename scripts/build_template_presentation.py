"""Create an editable three-minute pitch in the supplied official PowerPoint template."""

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


def main():
    from scripts.build_four_slide_presentation import main as build_four
    build_four()


if __name__ == '__main__':
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    main()
