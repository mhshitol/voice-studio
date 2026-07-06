"""Voice Studio — a local, free ElevenLabs-style voiceover app.

Runs Chatterbox TTS on your own GPU with a browser UI:
voice library with demos, voice cloning, per-line emotion "vibes",
ElevenLabs-style break tags, and MP3 export.

All paths are relative to this file, so the project folder can live anywhere.
"""
import re
from pathlib import Path

import gradio as gr
import numpy as np
import soundfile as sf

BASE = Path(__file__).resolve().parent
VOICES_DIR = BASE / "voices"
PREVIEW_DIR = VOICES_DIR / "previews"
OUT_ROOT = BASE / "output"
VOICES_DIR.mkdir(exist_ok=True)
OUT_ROOT.mkdir(exist_ok=True)

BREAK = re.compile(r'<break\s+time="([\d.]+)s?"\s*/?\s*>|\[pause\s+([\d.]+)\]')
VIBE_TAG = re.compile(r'^\[(horror|dramatic|chill|neutral|natural|excited)\]\s*', re.I)

# vibe -> (exaggeration, cfg_weight)
# 0.5/0.5 is the model's natural sweet spot — vibes only nudge it slightly.
# The mood should come from the WRITING (short sentences, ellipses) and the voice choice.
VIBES = {
    "natural":  (0.50, 0.50),
    "horror":   (0.55, 0.45),
    "dramatic": (0.55, 0.45),
    "chill":    (0.45, 0.50),
    "excited":  (0.58, 0.48),
}

PREVIEW_TEXT = (
    'Every story starts the same way... <break time="0.4s" /> with something small. '
    'A knock at the door. A mark on the wall. A light that should not be on. '
    '<break time="0.5s" /> And by the time you notice it... <break time="0.4s" /> '
    "it has already noticed you. <break time=\"0.5s\" /> "
    "But hey — maybe it's nothing. Sleep well tonight."
)

_model = None


def get_model():
    global _model
    if _model is None:
        from chatterbox.tts import ChatterboxTTS
        _model = ChatterboxTTS.from_pretrained(device="cuda")
    return _model


def list_voices():
    return ["Default (built-in)"] + sorted(p.stem for p in VOICES_DIR.glob("*.wav"))


def voice_path(name):
    return None if name == "Default (built-in)" else str(VOICES_DIR / f"{name}.wav")


def _polish(seg, sr):
    """Trim model's own silence padding, normalize loudness, add tiny fades to avoid clicks."""
    import librosa
    seg, _ = librosa.effects.trim(seg, top_db=35)
    if len(seg) == 0:
        return seg
    rms = np.sqrt(np.mean(seg ** 2))
    if rms > 1e-5:
        seg = seg * (0.06 / rms)          # consistent loudness across segments
    peak = np.abs(seg).max()
    if peak > 0.95:
        seg = seg / peak * 0.95           # guard against clipping
    fade = min(int(sr * 0.012), len(seg) // 2)
    if fade > 0:
        seg[:fade] *= np.linspace(0.0, 1.0, fade)
        seg[-fade:] *= np.linspace(1.0, 0.0, fade)
    return seg


def render_text(text, exaggeration, cfg, voice):
    """Synthesize text, honoring <break time="Xs"/> and [pause X] as exact silence."""
    m = get_model()
    sr = m.sr
    kw = {}
    vp = voice_path(voice)
    if vp:
        kw["audio_prompt_path"] = vp

    def speak(seg_text):
        wav = m.generate(seg_text, exaggeration=exaggeration, cfg_weight=cfg, **kw)
        return _polish(wav.squeeze(0).cpu().numpy(), sr)

    parts, pos = [], 0
    for mt in BREAK.finditer(text):
        seg = text[pos:mt.start()].strip()
        if seg:
            parts.append(speak(seg))
        parts.append(np.zeros(int(sr * float(mt.group(1) or mt.group(2))), dtype=np.float32))
        pos = mt.end()
    tail = text[pos:].strip()
    if tail:
        parts.append(speak(tail))
    return (np.concatenate(parts) if parts else np.zeros(1, dtype=np.float32)), sr


def preview_voice(voice, vibe):
    PREVIEW_DIR.mkdir(exist_ok=True)
    safe = re.sub(r'[^\w-]', '_', f"{voice}_{vibe}")
    out = PREVIEW_DIR / f"{safe}.mp3"
    if not out.exists():
        ex, cf = VIBES[vibe]
        audio, sr = render_text(PREVIEW_TEXT, ex, cf, voice)
        sf.write(out, audio, sr)
    return str(out)


def add_voice(file, name):
    if not file:
        return gr.update(), gr.update(), "Upload an audio file first."
    name = re.sub(r'[^\w-]', '_', (name or "").strip()) or "My-Voice"
    dest = VOICES_DIR / f"{name}.wav"
    import librosa
    y, sr = librosa.load(file, sr=24000, mono=True, duration=20.0)
    sf.write(dest, y, sr)
    voices = list_voices()
    return (gr.update(choices=voices, value=name),
            gr.update(choices=voices, value=name),
            f"Added voice '{name}'. Select it and preview.")


def generate(script, voice, default_vibe, project):
    lines = [l.strip() for l in script.splitlines() if l.strip() and not l.strip().startswith("#")]
    if not lines:
        return None, None, "Script is empty."
    project = re.sub(r'[^\w-]', '_', (project or "").strip()) or "untitled"
    outdir = OUT_ROOT / project
    outdir.mkdir(parents=True, exist_ok=True)
    log, combined, sr = [], [], 24000
    for i, line in enumerate(lines, 1):
        vibe = default_vibe
        mt = VIBE_TAG.match(line)
        if mt:
            vibe = mt.group(1).lower()
            if vibe == "neutral":
                vibe = "natural"
            line = line[mt.end():]
        ex, cf = VIBES[vibe]
        audio, sr = render_text(line, ex, cf, voice)
        sf.write(outdir / f"clip_{i:02d}.wav", audio, sr)
        combined.append(audio)
        combined.append(np.zeros(int(sr * 0.3), dtype=np.float32))
        log.append(f"clip_{i:02d}  [{vibe}]  {len(audio)/sr:5.1f}s  {BREAK.sub('|', line)[:50]}")
    full = np.concatenate(combined)
    mp3_path = outdir / f"{project}.mp3"
    sf.write(mp3_path, full, sr)
    total = len(full) / sr
    info = (f"TOTAL: {total:.1f}s  |  voice: {voice}\n"
            f"MP3: {mp3_path}\n"
            f"Per-shot clips (for video editing): {outdir}\\clip_01.wav ...\n\n" + "\n".join(log))
    return str(mp3_path), str(mp3_path), info


EXAMPLE = """# One line = one clip. Start a line with [horror] [dramatic] [chill] [natural] [excited] to set its vibe.
# Pauses: <break time="0.4s" /> or [pause 0.4] - both are baked into the audio.
[dramatic] It's three A M. You wake up... [pause 0.4] and you can't move.
[horror] And something is sitting on your chest.
[chill] Today we call it sleep paralysis. Totally harmless... probably.
"""

with gr.Blocks(title="Voice Studio") as demo:
    gr.Markdown("# 🎙️ Voice Studio\n*Your local, free ElevenLabs — runs on your GPU, no subscription, no limits*")

    with gr.Tab("1 · Pick a voice"):
        with gr.Row():
            voice_dd = gr.Dropdown(choices=list_voices(), value="Default (built-in)", label="Voice", scale=3)
            vibe_prev = gr.Dropdown(choices=list(VIBES), value="natural", label="Demo vibe", scale=1)
            prev_btn = gr.Button("▶ Hear this voice (15s demo)", variant="primary", scale=1)
        prev_audio = gr.Audio(label="Voice demo — play / pause / seek", type="filepath", interactive=False)
        prev_btn.click(preview_voice, [voice_dd, vibe_prev], prev_audio)

        gr.Markdown("### Add your own voice (10–20s of clean speech — a phone recording works)")
        with gr.Row():
            up = gr.Audio(label="Upload or record", type="filepath", sources=["upload", "microphone"], scale=2)
            up_name = gr.Textbox(label="Voice name", placeholder="My-Voice", scale=1)
            up_btn = gr.Button("Add voice", scale=1)
        up_status = gr.Markdown()

    with gr.Tab("2 · Generate voiceover"):
        with gr.Row():
            voice_dd2 = gr.Dropdown(choices=list_voices(), value="Default (built-in)", label="Voice", scale=2)
            vibe_dd = gr.Dropdown(choices=list(VIBES), value="natural", label="Default vibe (untagged lines)", scale=2)
            project_tb = gr.Textbox(label="Project name (file name)", value="my-video", scale=2)
        script_tb = gr.Textbox(label="Script — ElevenLabs style, breaks and vibe tags supported", value=EXAMPLE, lines=14)
        gen_btn = gr.Button("🎬 Generate MP3", variant="primary")
        out_audio = gr.Audio(label="Result — play / pause / seek", type="filepath", interactive=False)
        dl_file = gr.File(label="⬇ Download MP3")
        log_tb = gr.Textbox(label="Details", lines=8)
        gen_btn.click(generate, [script_tb, voice_dd2, vibe_dd, project_tb], [out_audio, dl_file, log_tb])

    up_btn.click(add_voice, [up, up_name], [voice_dd, voice_dd2, up_status])
    gr.Markdown("Vibes: **natural** sweet spot · **horror** slow+dark · **dramatic** big reveals · **chill** relaxed · **excited** energetic")

demo.launch(server_name="127.0.0.1", server_port=7860)
