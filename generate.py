"""Command-line voiceover generator (same engine as the Studio UI).

Usage:  voiceover.bat path\\to\\script.txt [--voice Jacob] [--vibe natural]

Script format: one line = one clip. Lines may start with a vibe tag
([horror] [dramatic] [chill] [natural] [excited]) and may contain
<break time="0.4s" /> or [pause 0.4] tags for exact silences.
"""
import argparse
import re
from pathlib import Path

import numpy as np
import soundfile as sf

BASE = Path(__file__).resolve().parent

BREAK = re.compile(r'<break\s+time="([\d.]+)s?"\s*/?\s*>|\[pause\s+([\d.]+)\]')
VIBE_TAG = re.compile(r'^\[(horror|dramatic|chill|neutral|natural|excited)\]\s*', re.I)
VIBES = {
    "natural":  (0.50, 0.50),
    "horror":   (0.55, 0.45),
    "dramatic": (0.55, 0.45),
    "chill":    (0.45, 0.50),
    "excited":  (0.58, 0.48),
}

p = argparse.ArgumentParser(description="Generate numbered VO clips from a script file (one line = one clip)")
p.add_argument("script", help="path to .txt script; blank lines and #comments are skipped")
p.add_argument("--vibe", default="natural", choices=list(VIBES), help="default vibe for untagged lines")
p.add_argument("--voice", default=None, help="voice name from the voices folder (e.g. Jacob), or path to a reference wav")
a = p.parse_args()

from chatterbox.tts import ChatterboxTTS  # slow import, after arg errors

model = ChatterboxTTS.from_pretrained(device="cuda")
sr = model.sr

kw = {}
if a.voice:
    ref = Path(a.voice)
    if not ref.exists():
        ref = BASE / "voices" / f"{a.voice}.wav"
    if not ref.exists():
        raise SystemExit(f"voice not found: {a.voice}")
    kw["audio_prompt_path"] = str(ref)


def polish(seg):
    import librosa
    seg, _ = librosa.effects.trim(seg, top_db=35)
    if len(seg) == 0:
        return seg
    rms = np.sqrt(np.mean(seg ** 2))
    if rms > 1e-5:
        seg = seg * (0.06 / rms)
    peak = np.abs(seg).max()
    if peak > 0.95:
        seg = seg / peak * 0.95
    fade = min(int(sr * 0.012), len(seg) // 2)
    if fade > 0:
        seg[:fade] *= np.linspace(0.0, 1.0, fade)
        seg[-fade:] *= np.linspace(1.0, 0.0, fade)
    return seg


def render_line(line, ex, cf):
    parts, pos = [], 0
    for mt in BREAK.finditer(line):
        seg = line[pos:mt.start()].strip()
        if seg:
            parts.append(polish(model.generate(seg, exaggeration=ex, cfg_weight=cf, **kw).squeeze(0).cpu().numpy()))
        parts.append(np.zeros(int(sr * float(mt.group(1) or mt.group(2))), dtype=np.float32))
        pos = mt.end()
    tail = line[pos:].strip()
    if tail:
        parts.append(polish(model.generate(tail, exaggeration=ex, cfg_weight=cf, **kw).squeeze(0).cpu().numpy()))
    return np.concatenate(parts) if parts else np.zeros(0, dtype=np.float32)


src = Path(a.script)
lines = [l.strip() for l in src.read_text(encoding="utf-8").splitlines()]
lines = [l for l in lines if l and not l.startswith("#")]
outdir = src.parent / (src.stem + "_vo")
outdir.mkdir(exist_ok=True)

total = 0.0
for i, line in enumerate(lines, 1):
    vibe = a.vibe
    mt = VIBE_TAG.match(line)
    if mt:
        vibe = mt.group(1).lower()
        if vibe == "neutral":
            vibe = "natural"
        line = line[mt.end():]
    ex, cf = VIBES[vibe]
    audio = render_line(line, ex, cf)
    out = outdir / f"clip_{i:02d}.wav"
    sf.write(out, audio, sr)
    dur = len(audio) / sr
    total += dur
    print(f"{out.name}  [{vibe}]  {dur:5.1f}s  {BREAK.sub('|', line)[:55]}")

print(f"done: {len(lines)} clips, {total:.1f}s total -> {outdir}")
