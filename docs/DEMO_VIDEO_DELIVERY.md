# Completed demo video

FinPilot AI — Financial Survival Copilot, presented for
**Md. Meherab Hossain Talukder — Solo Participant**.

- Runtime: approximately **2:53** (172.864 seconds planned timeline).
- Picture: **1920×1080, 30 fps, H.264 MP4**, with fast-start metadata.
- Sound: English neural narration, Microsoft `en-US-GuyNeural` via edge-tts;
  AAC video audio, normalized toward -16 LUFS / -1 dBTP. No background music.
- Narration is generated speech, not a recording or clone of the creator's voice.
- Captions: burned into the video, plus a separate SRT with non-overlapping cues.
- Three scenes record the actual live public landing/demo workflow, including a
  genuine CSRF-protected seven-day-delay comparison. No production ledger or chat
  records were created or changed; this public demo is stateless and synthetic.
- The private AI sequence uses the supplied saved Groq response excerpt, explicitly
  labeled as a synthetic workspace capture. No new private inference was made.
- Opening, explanation and closing cards are native HTML renders, using the
  original event sticker unchanged. Saved Business/mobile screenshots are synthetic.

## Files

- `static/submission/video/index.html` — browser video player and downloads.
- `static/submission/video/FinPilot_AI_Demo_1080p.mp4` — finished video.
- `static/submission/video/FinPilot_AI_Voiceover.mp3` — narration track.
- `static/submission/video/FinPilot_AI_English.srt` — timed English captions.
- `static/submission/video/FinPilot_AI_Final_Script.txt` — exact narration/timestamps.
- `static/submission/video/verification.json` — technical and provenance checks.
- `static/submission/finpilot-demo-video-package.zip` — complete delivery archive.

After deployment, browser player:
<https://finpilot-ai-web.onrender.com/static/submission/video/index.html>.

Direct MP4:
<https://finpilot-ai-web.onrender.com/static/submission/video/FinPilot_AI_Demo_1080p.mp4>.

## Validation and limits

The complete MP4 was decoded with FFmpeg. Checks cover H.264/AAC, 1080p output,
caption timing, absence of black gaps over 0.7 seconds and absence of silence gaps
over five seconds. Representative opening, dashboard, scenario, Advisor and closing
frames were extracted for visual review. A detected cue overlap was corrected;
the final render uses non-overlapping cues and a dark caption background.

This is technical validation and sampled visual review, not a claim of independent
human listening or a guarantee of pronunciation. Preview before publishing.
No YouTube upload or Devpost submission has been performed. To fill Devpost's
optional YouTube field, upload the MP4 to your YouTube account and use that video URL.
The live MP4 link is not a YouTube URL.

## Reproduction

Optional **local production tools**, not application runtime dependencies:

```powershell
.venv\Scripts\python -m pip install edge-tts imageio-ffmpeg playwright
.venv\Scripts\python scripts/produce_demo_video.py
```

The script sends only the public narration text to Microsoft's speech service,
records public synthetic pages and edits locally with FFmpeg. It never reads `.env`
or requests private login credentials. Local saved synthetic Business/mobile captures
from the earlier browser checks are required for the readiness card. Intermediate
audio, genuine browser recordings, source HTML cards, captions and encoding logs
are in ignored `test-results/video/`. Phase flags allow capture/render/verification
to resume using these intermediate files; the Python script is the editable timeline.
