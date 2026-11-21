# Instagram · jurnalalimentar.fit

- `plan.md`: content calendar (also copied to `~/.claude/instagram/plan.md` for the `/ig-*` skills)
- `engine/`: reel renderers (Python + PIL + ffmpeg) and the app captures they use
  - `reel3.py`: Premium plan reel (motion design), `reel4.py`: cinematic overview, `reel2.py`: shared engine
  - `python3 engine/reel4.py out.mp4` renders a reel; `python3 engine/reel4.py x 1.0,5.0` writes preview frames
- `captions/`: linted captions, `reels/`: scripts
- `log.md`: what was actually posted (filled in after each post)

Voice: ElevenLabs "Anca – Warm Voice for Every Story" (voice_id GRHbHyXbUO8nF4YexVTa), model eleven_v4.
