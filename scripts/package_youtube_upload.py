"""Package the finished demo, thumbnail and copy-ready YouTube metadata."""
from pathlib import Path
import re
import zipfile

from PIL import Image


def main():
    document = Path('docs/YOUTUBE_UPLOAD_DETAILS.md').read_text(encoding='utf-8')
    blocks = re.findall(r'```text\n(.*?)\n```', document, flags=re.S)
    assert len(blocks) == 3
    title, description, tags = blocks
    assert len(title) <= 100 and len(tags) <= 500
    assert description.startswith('Can an expected client payment')
    thumbnail = Path('static/submission/finpilot-youtube-thumbnail.png')
    with Image.open(thumbnail) as image:
        assert image.width >= 640 and abs(image.width/image.height - 16/9) < .002
    assert thumbnail.stat().st_size < 2_000_000
    folder = Path('static/submission/video')
    names = ['YouTube_Title.txt', 'YouTube_Description.txt', 'YouTube_Tags.txt']
    for name, text in zip(names, blocks, strict=True):
        (folder/name).write_text(text+'\n', encoding='utf-8')
    destination = Path('static/submission/finpilot-youtube-upload-kit.zip')
    with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(folder/'FinPilot_AI_Demo_1080p.mp4','FinPilot_AI_Demo_1080p.mp4')
        archive.write(thumbnail,thumbnail.name)
        archive.write(folder/'FinPilot_AI_English.srt','FinPilot_AI_English.srt')
        for name in names:
            archive.write(folder/name,name)
        archive.writestr('README.txt',
            'FinPilot AI — YouTube Upload Kit\n\n'
            '1. Upload FinPilot_AI_Demo_1080p.mp4 in YouTube Studio.\n'
            '2. Copy the complete contents of YouTube_Title.txt and YouTube_Description.txt\n'
            '   into their corresponding fields. Copy YouTube_Tags.txt into Tags.\n'
            '3. Use finpilot-youtube-thumbnail.png as the custom thumbnail.\n'
            '4. Video language: English. Category: Science & Technology.\n'
            '5. This general-audience finance demo is not made for kids.\n'
            '6. Optional: add the timed SRT; visible captions are already in the MP4.\n'
            '7. Choose Unlisted for link sharing with judges, or Public for public access.\n'
            '   Do not choose Private if judges need access. Complete required disclosures\n'
            '   truthfully; the description identifies AI narration and synthetic sources.\n'
            '8. Preview, finish uploading, copy the actual YouTube watch URL and paste it\n'
            '   into Devpost\'s Product Demo YouTube Link field.\n\n'
            'Created by Md. Meherab Hossain Talukder — Solo Participant.\n'
            'This kit has not uploaded anything to YouTube or submitted to Devpost.\n')
    with zipfile.ZipFile(destination) as archive:
        assert archive.testzip() is None and len(archive.namelist()) == 7
    print(f'YouTube kit ready: {destination.stat().st_size:,} bytes; title {len(title)} characters; tags {len(tags)} characters.')


if __name__ == '__main__':
    main()
