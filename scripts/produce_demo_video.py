"""Render the public/synthetic FinPilot demo with neural narration and captions.

Optional local tools: pip install edge-tts imageio-ffmpeg playwright
No production credentials or private financial data are accessed. Narration text
is sent to Microsoft's speech service through edge-tts. Video editing uses FFmpeg.
"""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import time
import wave
import zipfile

import edge_tts
import imageio_ffmpeg
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / 'test-results/video'
OUT = ROOT / 'static/submission/video'
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
VOICE = 'en-US-GuyNeural'
TARGETS = [20, 20, 25, 30, 30, 20, 15]
LABELS = [
    'THE PROBLEM', 'PUBLIC DEMO | SYNTHETIC DATA', 'PAID CASH VS EXPECTED INCOME',
    'REAL DEMO | HYPOTHETICAL SCENARIO', 'SAVED GROQ RESPONSE | SYNTHETIC WORKSPACE',
    'ACTUAL SYNTHETIC WORKSPACE CAPTURES', 'TRY FINPILOT AI',
]


def run(args, log):
    with (WORK / log).open('w', encoding='utf-8') as handle:
        result = subprocess.run([FFMPEG, '-y', '-hide_banner', *map(str, args)],
                                cwd=WORK, stdout=handle, stderr=handle)
    if result.returncode:
        raise RuntimeError((WORK / log).read_text(encoding='utf-8')[-3500:])


def seconds(path):
    with wave.open(str(path), 'rb') as audio:
        return audio.getnframes() / audio.getframerate()


def scripts():
    source = (ROOT / 'docs/VIDEO_CREATION_MASTER_PROMPT.md').read_text(encoding='utf-8')
    paragraphs = re.findall('Voiceover:\\s*“(.*?)”', source, flags=re.S)
    assert len(paragraphs) == 7
    return [' '.join(text.split()) for text in paragraphs]


async def narrate(texts):
    semaphore = asyncio.Semaphore(2)

    async def one(index, text):
        async with semaphore:
            mp3 = WORK / f'voice-{index:02}.mp3'
            timings = WORK / f'words-{index:02}.json'
            if mp3.exists() and timings.exists():
                return
            spoken = text.replace('FinPilot', 'Fin Pilot').replace('Groq', 'Grock')
            spoken = spoken.replace('Md. Meherab', 'Meherab')
            words = []
            request = edge_tts.Communicate(spoken, VOICE, rate='-12%',
                                           boundary='WordBoundary', receive_timeout=30)
            with mp3.open('wb') as stream:
                async for chunk in request.stream():
                    if chunk['type'] == 'audio':
                        stream.write(chunk['data'])
                    elif chunk['type'] == 'WordBoundary':
                        words.append({key: chunk[key] for key in ('offset', 'duration', 'text')})
            assert mp3.stat().st_size > 1000 and len(words) > 20
            timings.write_text(json.dumps(words), encoding='utf-8')
            print(f'Neural voice scene {index} generated ({len(words)} spoken words).', flush=True)

    await asyncio.gather(*(one(i, text) for i, text in enumerate(texts, 1)))


def cue_text(words):
    return ' '.join(word['text'] for word in words).replace('Fin Pilot', 'FinPilot').replace('Grock', 'Groq')


def cues(index):
    words = json.loads((WORK / f'words-{index:02}.json').read_text(encoding='utf-8'))
    batch = []
    result = []
    for word in words:
        if batch and (len(cue_text(batch + [word])) > 65 or len(batch) >= 10):
            result.append(batch)
            batch = []
        batch.append(word)
    if batch:
        result.append(batch)
    timed = [(group[0]['offset']/1e7 + .4,
              (group[-1]['offset']+group[-1]['duration'])/1e7 + .55,
              cue_text(group)) for group in result]
    return [(start, min(end, timed[i+1][0]-.03) if i+1 < len(timed) else end, text)
            for i, (start, end, text) in enumerate(timed)]


def ass_time(value):
    total = round(value * 100)
    return f'{total//360000}:{total//6000%60:02}:{total//100%60:02}.{total%100:02}'


def srt_time(value):
    total = round(value * 1000)
    return f'{total//3600000:02}:{total//60000%60:02}:{total//1000%60:02},{total%1000:03}'


def prepare_audio(texts):
    durations = []
    all_cues = []
    cursor = 0
    header = '''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,38,&H00FFFFFF,&H00FFFFFF,&H202B1B0F,&H202B1B0F,0,0,0,0,100,100,0,0,3,2,0,2,100,100,32,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    transcript = []
    for index, text in enumerate(texts, 1):
        raw = WORK / f'raw-{index:02}.wav'
        run(['-i', WORK/f'voice-{index:02}.mp3', '-ar', 48000, '-ac', 1, raw], f'decode-{index}.log')
        duration = max(TARGETS[index-1], seconds(raw) + 1.2)
        durations.append(duration)
        run(['-i', raw, '-af', 'adelay=400:all=1,apad', '-t', f'{duration:.3f}',
             '-ar', 48000, '-ac', 1, WORK/f'audio-{index:02}.wav'], f'audio-{index}.log')
        scene_cues = cues(index)
        content = header + '\n'.join(
            f'Dialogue: 0,{ass_time(start)},{ass_time(end)},Default,,0,0,0,,{caption}'
            for start, end, caption in scene_cues
        ) + '\n'
        (WORK/f'scene-{index:02}.ass').write_text(content, encoding='utf-8-sig')
        all_cues.extend((start+cursor, end+cursor, caption) for start, end, caption in scene_cues)
        transcript.append(f'{srt_time(cursor)} — {srt_time(cursor+duration)}\n{text}\n')
        cursor += duration
    assert 150 <= sum(durations) < 180, durations
    assert all(start < end for start, end, _ in all_cues)
    assert all(all_cues[i][1] <= all_cues[i+1][0] for i in range(len(all_cues)-1))
    srt = '\n\n'.join(f'{i}\n{srt_time(start)} --> {srt_time(end)}\n{text}'
                        for i, (start, end, text) in enumerate(all_cues, 1)) + '\n'
    (OUT/'FinPilot_AI_English.srt').write_text(srt, encoding='utf-8')
    (OUT/'FinPilot_AI_Final_Script.txt').write_text(
        'FinPilot AI — Financial Survival Copilot\nMd. Meherab Hossain Talukder — Solo Participant\n'
        f'AI narration: Microsoft {VOICE}; not the founder’s voice.\n\n' + '\n'.join(transcript), encoding='utf-8')
    print(f'Final planned runtime: {sum(durations):.1f} seconds.', flush=True)
    return durations


def document(content, dark=False):
    background, foreground = ('#102b3c', '#fff') if dark else ('#f5faf9', '#142d42')
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>
    *{{box-sizing:border-box}}body{{margin:0;width:1920px;height:1080px;padding:64px 80px 140px;background:{background};color:{foreground};font-family:Arial,sans-serif;overflow:hidden}}
    .eyebrow{{font-size:25px;letter-spacing:3px;font-weight:bold;color:#23bea5}}h1{{font-size:86px;line-height:1.08;letter-spacing:-3px;margin:28px 0}}h2{{font-size:57px;line-height:1.15;letter-spacing:-1px;margin:24px 0}}p{{font-size:32px;line-height:1.5;margin:18px 0}}.muted{{color:#78939f}}.mint{{color:#72e0c4}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:60px;align-items:center}}.box{{padding:32px;border:1px solid #3b5865;border-radius:22px;background:#1b3a4a;margin:20px 0}}.label{{font-size:22px;letter-spacing:1px;color:#c6e0e0}}.credit{{font-size:28px;margin-top:25px}}.sticker{{display:block;width:480px;height:auto;border-radius:12px;margin-top:30px}}.pill{{display:inline-block;padding:12px 20px;border-radius:18px;background:#dff5ec;color:#075e54;font-size:23px;font-weight:bold}}.shot{{display:block;width:100%;height:auto;border:1px solid #cde0df;border-radius:18px}}.footer{{font-size:22px;line-height:1.4;color:#607d8a;margin-top:16px}}.step{{font-size:28px;line-height:1.5;padding:24px;border-radius:14px;background:#e3f3ed;margin-bottom:20px}}.step strong{{display:block;color:#087e70;margin-bottom:6px}}
    </style></head><body>{content}</body></html>'''


def static_frames(page):
    sticker = (ROOT/'static/buildathon/yunet-aignite-buildathon-2026-sticker.jpeg').as_uri()
    excerpt = (ROOT/'static/submission/images/personal-advisor-excerpt.png').as_uri()
    business = (ROOT/'test-results/survival/dashboard-1440.png').as_uri()
    mobile = (ROOT/'test-results/sticker/dashboard-390.png').as_uri()
    scenes = {
        1: document(f'''<div class="eyebrow">FINPILOT AI · FINANCIAL SURVIVAL COPILOT</div><div class="grid" style="margin-top:40px"><div><h1>Expected income<br>isn't <span class="mint">available cash.</span></h1><p>A payment promise cannot cover<br>a bill that is due today.</p><div class="credit">Md. Meherab Hossain Talukder<br><span class="mint">Solo Participant</span></div><img class="sticker" src="{sticker}" alt="Original official event sticker"></div><div><div class="box"><div class="label">CLIENT PAYMENT</div><h2 style="margin-bottom:12px">Expected later</h2></div><div style="font-size:50px;text-align:center;color:#72e0c4">↓</div><div class="box"><div class="label">ESSENTIAL BILL</div><h2 style="margin-bottom:12px">Due sooner</h2></div><p style="color:#bad5dc;font-size:25px">Concept illustration · timing matters</p></div></div>''', True),
        5: document(f'''<div class="eyebrow">SAVED GROQ RESPONSE · SYNTHETIC PRIVATE WORKSPACE</div><h2>Calculations first. <span style="color:#087e70">Explanations second.</span></h2><div style="display:grid;grid-template-columns:340px 1fr;gap:38px;margin-top:36px"><div><div class="step"><strong>1. Records</strong>Authorized workspace evidence</div><div class="step"><strong>2. Calculate</strong>Deterministic dates and amounts</div><div class="step"><strong>3. Explain</strong>Conditional AI guidance</div><div class="step"><strong>4. You decide</strong>No autonomous money movement</div></div><div><img class="shot" src="{excerpt}"><div class="footer">Actual saved response excerpt; typography enlarged for presentation.<br>The account-free public demo uses deterministic explanations, not live AI.</div></div></div>'''),
        6: document(f'''<div class="eyebrow">PRACTICAL WORKFLOWS · RESPONSIVE DESIGN</div><h2>One clearer plan. On every screen.</h2><div style="display:grid;grid-template-columns:310px 1fr;gap:50px;margin-top:26px"><img src="{mobile}" style="height:660px;width:auto;border:1px solid #cde0df;border-radius:20px"><div><div style="height:555px;overflow:hidden;border:1px solid #cde0df;border-radius:20px"><img src="{business}" style="display:block;width:100%;height:auto"></div><p style="font-size:28px;margin:18px 0 8px">Separate workspaces · PDF / CSV / XLSX exports</p><span class="pill">368 PostgreSQL tests passed · 7 screen widths checked</span></div></div><div class="footer">Actual saved application captures · synthetic records</div>'''),
        7: document(f'''<div class="eyebrow">FINPILOT AI</div><h1 style="margin-top:90px">Make a clearer decision<br><span class="mint">before spending.</span></h1><p>Financial Survival Copilot</p><div class="credit">Md. Meherab Hossain Talukder · Solo Participant</div><div class="box" style="margin-top:40px"><div class="label">TRY THE ACCOUNT-FREE SYNTHETIC DEMO</div><p style="font-size:41px;font-weight:bold;color:#72e0c4">finpilot-ai-web.onrender.com/demo/personal/</p></div><p style="font-size:24px;color:#bad5dc">Decision support; estimates depend on recorded data and assumptions.</p><img class="sticker" style="width:390px" src="{sticker}">''', True),
    }
    for index, markup in scenes.items():
        path = WORK/f'frame-{index:02}.html'
        if index == 5:
            markup = markup.replace('</style>', '.step{font-size:24px;line-height:1.35;padding:20px;margin-bottom:16px}.shot{width:1200px;max-width:100%}</style>')
        path.write_text(markup, encoding='utf-8')
        page.goto(path.as_uri())
        page.locator('img').first.evaluate('(img)=>img.decode()')
        page.screenshot(path=str(WORK/f'frame-{index:02}.png'))
    print('Four full-resolution product film cards captured.', flush=True)


def capture(durations):
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='chromium')
        page = browser.new_page(viewport={'width':1920, 'height':1080})
        static_frames(page)
        page.close()
        origin = 'https://finpilot-ai-web.onrender.com'
        probe = browser.new_page()
        try:
            response = probe.goto(origin+'/demo/personal/', timeout=90000)
            assert response.status == 200
        except Exception:
            origin = 'https://finpilot-ai-sme-copilot.vercel.app'
            response = probe.goto(origin+'/demo/personal/', timeout=90000)
            assert response.status == 200
        probe.close()
        evidence = []
        for index in (2, 3, 4):
            destination = WORK/f'live-{index:02}.webm'
            metadata = WORK/f'live-{index:02}.json'
            if destination.exists() and metadata.exists():
                evidence.append(json.loads(metadata.read_text()))
                continue
            context = browser.new_context(viewport={'width':1440,'height':810},
                                          record_video_dir=str(WORK/'recordings'),
                                          record_video_size={'width':1440,'height':810})
            started = time.monotonic()
            page = context.new_page()
            page.goto(origin+('/' if index == 2 else '/demo/personal/'), wait_until='networkidle', timeout=90000)
            page.evaluate('document.fonts.ready')
            page.wait_for_timeout(500)
            trim = time.monotonic() - started
            content_start = time.monotonic()
            if index == 2:
                page.wait_for_timeout(4000)
                page.locator('a[href="/demo/personal/"]').first.click()
                page.wait_for_url('**/demo/personal/')
                page.wait_for_timeout(3000)
                page.locator('.personal-metrics').scroll_into_view_if_needed()
            elif index == 3:
                page.locator('.personal-metrics').evaluate('(el)=>window.scrollTo({top:el.getBoundingClientRect().top+scrollY-110,behavior:"smooth"})')
                for panel in page.locator('.personal-metrics article').all():
                    panel.hover()
                    page.wait_for_timeout(2200)
                page.locator('.personal-highlight').hover()
            else:
                page.locator('#id_scenario').scroll_into_view_if_needed()
                page.wait_for_timeout(1800)
                page.locator('#id_scenario').select_option('delay')
                page.wait_for_timeout(1200)
                page.locator('#id_delay_days').select_option('7')
                page.wait_for_timeout(1200)
                page.locator('#id_income_reference').select_option('demo-income')
                page.wait_for_timeout(1500)
                page.get_by_role('button',name='Compare synthetic scenario',exact=True).click()
                result = page.locator('#personal-result')
                result.wait_for()
                assert '2000.00' in result.inner_text() and '16000.00' in result.inner_text()
                result.evaluate('(el)=>window.scrollTo({top:el.getBoundingClientRect().top+scrollY-85,behavior:"smooth"})')
                page.wait_for_timeout(4000)
                result.locator('tr').filter(has_text='Reserve shortfall').hover()
            remaining = durations[index-1] - (time.monotonic()-content_start) + .8
            page.wait_for_timeout(max(1000, remaining*1000))
            video = page.video
            context.close()
            video.save_as(str(destination))
            record = {'scene':index,'origin':origin,'trim_start':trim,
                      'recorded_public_demo':True,'financial_writes':False,
                      'scenario_post':index == 4}
            metadata.write_text(json.dumps(record, indent=2), encoding='utf-8')
            evidence.append(record)
            print(f'Real public product footage recorded for scene {index}.', flush=True)
        browser.close()
    return evidence


def render(durations):
    shutil.copyfile('C:/Windows/Fonts/arial.ttf', WORK/'arial.ttf')
    for index, duration in enumerate(durations, 1):
        destination = WORK/f'segment-{index:02}.mp4'
        label = WORK/f'label-{index:02}.txt'
        label.write_text(LABELS[index-1], encoding='utf-8')
        live = index in (2, 3, 4)
        if live:
            meta = json.loads((WORK/f'live-{index:02}.json').read_text())
            inputs = ['-ss', f"{meta['trim_start']:.3f}", '-i', WORK/f'live-{index:02}.webm']
        else:
            inputs = ['-loop', '1', '-framerate', 30, '-i', WORK/f'frame-{index:02}.png']
        filters = 'fps=30,scale=1920:1080,setsar=1,tpad=stop_mode=clone:stop_duration=3'
        if live:
            filters += f',drawbox=x=0:y=0:w=iw:h=55:color=0x102b3c:t=fill,drawtext=fontfile=arial.ttf:textfile=label-{index:02}.txt:fontcolor=0x8fe9d3:fontsize=25:x=42:y=14'
        filters += f',fade=t=in:st=0:d=0.22,subtitles=scene-{index:02}.ass,format=yuv420p'
        run([*inputs, '-i', WORK/f'audio-{index:02}.wav', '-map','0:v:0','-map','1:a:0',
             '-vf', filters, '-t', f'{duration:.3f}', '-c:v','libx264','-preset','veryfast',
             '-crf','22','-threads','2','-c:a','aac','-b:a','160k','-ar','48000',destination],
            f'render-{index}.log')
        print(f'Scene {index} rendered: {duration:.1f}s, captions included.', flush=True)
    playlist = WORK/'concat.txt'
    playlist.write_text('\n'.join(f"file 'segment-{index:02}.mp4'" for index in range(1,8)), encoding='utf-8')
    final = OUT/'FinPilot_AI_Demo_1080p.mp4'
    run(['-f','concat','-safe','0','-i',playlist,'-map','0:v:0','-map','0:a:0',
         '-c:v','copy','-af','loudnorm=I=-16:TP=-1:LRA=11','-c:a','aac','-b:a','160k',
         '-ar','48000','-movflags','+faststart',final], 'final-mux.log')
    run(['-i',final,'-vn','-c:a','libmp3lame','-b:a','192k',OUT/'FinPilot_AI_Voiceover.mp3'], 'voiceover-export.log')
    print(f'Final MP4 ready: {final} ({final.stat().st_size:,} bytes).', flush=True)
    return final


def verify(final, durations, footage):
    run(['-i',final,'-vf','blackdetect=d=0.7:pix_th=0.05',
         '-af','silencedetect=noise=-45dB:d=5','-f','null','-'], 'full-decode-qa.log')
    log = (WORK/'full-decode-qa.log').read_text(encoding='utf-8')
    assert '1920x1080' in log and 'h264' in log and 'aac' in log
    assert 'black_start:' not in log, 'Unexpected black section; inspect QA log.'
    assert 'silence_start:' not in log, 'Unexpected long silence; inspect QA log.'
    assert final.stat().st_size < 100_000_000
    for index in (1, 3, 4, 5, 7):
        offset = sum(durations[:index-1]) + min(10, durations[index-1]/2)
        run(['-ss',f'{offset:.3f}','-i',final,'-frames:v','1',WORK/f'qa-scene-{index:02}.png'], f'qa-frame-{index}.log')
    report = {'duration_seconds':round(sum(durations),3),'resolution':'1920x1080',
              'fps':30,'video_codec':'H.264','audio_codec':'AAC','voice':VOICE,
              'synthetic_neural_voice':True,'captions_burned_in':True,
              'full_file_decode_passed':True,'no_black_gaps_over_0_7s':True,
              'no_silence_gaps_over_5s':True,'public_footage':footage,
              'private_ai':'Saved verified synthetic response excerpt; no new private inference.',
              'uploaded_to_youtube':False,'submitted_to_devpost':False,
              'bytes':final.stat().st_size,
              'sha256':hashlib.sha256(final.read_bytes()).hexdigest()}
    (OUT/'verification.json').write_text(json.dumps(report,indent=2), encoding='utf-8')
    print('Full-file decode, codecs, caption timeline and gap checks passed.', flush=True)


def package_delivery():
    names = ['FinPilot_AI_Demo_1080p.mp4','FinPilot_AI_Voiceover.mp3',
             'FinPilot_AI_English.srt','FinPilot_AI_Final_Script.txt','verification.json']
    destination = ROOT/'static/submission/finpilot-demo-video-package.zip'
    with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for name in names:
            archive.write(OUT/name, name)
        archive.writestr('README.txt',
            'FinPilot AI — Financial Survival Copilot\n'
            'Md. Meherab Hossain Talukder — Solo Participant\n\n'
            'Play FinPilot_AI_Demo_1080p.mp4. Runtime approximately 2:53.\n'
            'English neural narration and burned-in captions are included.\n'
            'The MP3, SRT and exact narration are supplied separately for editing.\n'
            'Public footage uses the actual synthetic demo. The private AI scene is\n'
            'a labeled saved verified Groq response, not a new live inference.\n'
            'AI narration is not the creator\'s voice. No YouTube upload has been made.\n'
            'Preview before publishing, then upload the MP4 to your own YouTube account\n'
            'if you want to provide a YouTube link on Devpost.\n')
    with zipfile.ZipFile(destination) as archive:
        assert archive.testzip() is None and len(archive.namelist()) == 6
    print(f'Complete delivery ZIP ready ({destination.stat().st_size:,} bytes).', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',choices=['all','voice','capture','render','verify'],default='all')
    args = parser.parse_args()
    WORK.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    texts = scripts()
    if args.phase in ('all','voice'):
        asyncio.run(narrate(texts))
    durations = prepare_audio(texts)
    if args.phase in ('all','capture'):
        evidence = capture(durations)
        (WORK/'footage.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
    if args.phase in ('all','render'):
        render(durations)
    if args.phase in ('all','verify'):
        verify(OUT/'FinPilot_AI_Demo_1080p.mp4',durations,
               json.loads((WORK/'footage.json').read_text()))
        package_delivery()


if __name__ == '__main__':
    main()
