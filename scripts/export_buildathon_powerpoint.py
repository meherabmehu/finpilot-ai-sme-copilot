"""Optional presentation export: pip install python-pptx; run the HTML exporter first.

Slides retain the rendered HTML design as images. Cover presenter text is editable;
edit other content in the HTML source and regenerate the slide images.
"""
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt


def main():
    presentation = Presentation()
    presentation.slide_width = Inches(13.333333)
    presentation.slide_height = Inches(7.5)
    for index in range(1, 6):
        slide = presentation.slides.add_slide(presentation.slide_layouts[6])
        slide.shapes.add_picture(
            str(Path('test-results/buildathon-slides') / f'slide-{index}.png'),
            0, 0, width=presentation.slide_width, height=presentation.slide_height,
        )
        if index == 1:
            box = slide.shapes.add_textbox(Inches(64 / 96), Inches(580 / 96), Inches(580 / 96), Inches(70 / 96))
            box.fill.solid()
            box.fill.fore_color.rgb = RGBColor.from_string('122D3E')
            box.line.fill.background()
            frame = box.text_frame
            frame.margin_left = frame.margin_right = frame.margin_top = frame.margin_bottom = 0
            for offset, (text, size) in enumerate([
                ('Md. Meherab Hossain Talukder', 16.5), ('Solo Participant', 12),
            ]):
                paragraph = frame.paragraphs[0] if offset == 0 else frame.add_paragraph()
                paragraph.text = text
                paragraph.space_before = Pt(5)
                paragraph.font.name = 'Arial'
                paragraph.font.size = Pt(size)
                paragraph.font.bold = True
                paragraph.font.color.rgb = RGBColor(255, 255, 255)
    destination = Path('static/submission/finpilot-aignite-2026.pptx')
    presentation.core_properties.author = 'Md. Meherab Hossain Talukder'
    presentation.core_properties.title = 'FinPilot AI — YUNet AIgnite 2026'
    presentation.save(destination)
    assert len(Presentation(destination).slides) == 5
    print('Five-slide PowerPoint created with editable cover presenter text.')


if __name__ == '__main__':
    main()
