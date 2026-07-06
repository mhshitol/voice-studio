# 🎙️ Voice Studio

**Your own free ElevenLabs — running locally on your GPU.**

Voice Studio is a simple browser app that turns written scripts into natural-sounding voiceovers. It runs [Chatterbox TTS](https://github.com/resemble-ai/chatterbox) (the open-source model that beats ElevenLabs in blind listening tests) entirely on your own computer:

-  **Free forever** — no subscription, no character limits, no credits
-  **Private** — nothing leaves your machine
-  **9 ready-made human voices** + clone any voice from a 10-second recording
-  **ElevenLabs-style break tags** — dramatic pauses baked into the audio
-  **Made for video creators** — outputs one MP3 *and* per-shot clips for your editor

![screenshot placeholder](docs/screenshot.png)

---

## What you need

- Windows PC with an **NVIDIA GPU** (8 GB VRAM recommended, e.g. RTX 3060/4060/5060)
- **Python 3.11+** — [download here](https://www.python.org/downloads/)
- ~8 GB of free disk space (the AI model is downloaded on first run)

## Install (one time, ~10 minutes)

Open a terminal in the project folder and run:

```bat
:: 1. Create an isolated Python environment inside the project
python -m venv venv

:: 2. Install the app
venv\Scripts\python.exe -m pip install -r requirements.txt

:: 3. Replace the CPU-only torch with the CUDA (GPU) build
venv\Scripts\python.exe -m pip install --upgrade torch torchaudio --index-url https://download.pytorch.org/whl/cu128
```

> **Note for RTX 50-series (Blackwell) cards:** the cu128 build above is required — the default PyTorch won't see your GPU.

## Run

Double-click **`studio.bat`** (or run it from a terminal).
Your browser opens at `http://127.0.0.1:7860`. The first generation downloads the voice model (~3 GB) and takes a minute; after that it's fast.

---

## How to use

### Tab 1 — Pick a voice

Choose a voice from the dropdown and press **"▶ Hear this voice"** to play a 15-second demo. The included voices (William, Kate, Edward, Mark, Nora, Jacob, Peter, Julia, David) were cut from public-domain LibriVox audiobook narrations — real human voices, legally safe to use.

**Clone your own voice:** record 10–20 seconds of clean speech (a phone memo works), upload it or record straight from the mic, give it a name — done. It appears in the dropdown.

### Tab 2 — Generate voiceover

Write your script — **one line becomes one audio clip**:

```
# Lines starting with # are comments.
[dramatic] It's three A M. You wake up... [pause 0.4] and you can't move.
[horror] And something is sitting on your chest.
[chill] Today we call it sleep paralysis. Totally harmless... probably.
```

- **Vibe tags** at the start of a line set its emotion: `[natural]` `[horror]` `[dramatic]` `[chill]` `[excited]`
- **Pause tags** anywhere in a line insert exact silence: `[pause 0.4]` or ElevenLabs-style `<break time="0.4s" />`
- **Ellipses (...)** make the voice itself hesitate — combine both for dramatic pacing

Press **🎬 Generate MP3**. You get:
- A player to listen immediately (regenerate as often as you like — it's free)
- A **download** button for the MP3
- Numbered per-line clips (`clip_01.wav`, `clip_02.wav`, ...) in `output/<project-name>/` — drop them onto your video editor timeline, one clip per shot

### Command line (optional)

```bat
voiceover.bat scripts\my-video.txt --voice Jacob --vibe natural
```

Generates the same numbered clips next to the script file.

---

## Tips for natural results

1. **Stay close to the `natural` vibe.** Extreme emotion settings make TTS sound slow and fake. Let the *writing* act: short sentences, ellipses, pauses.
2. **Write for the ear:** "He passed two years ago. I moved back in this spring." beats a long formal sentence.
3. **Put break tags between sentences,** not mid-sentence. Inside a sentence, use `...` instead.
4. **Regenerate freely.** Every generation varies slightly — a weird line usually fixes itself on the second try.
5. **Numbers:** write them out ("three forty-one", not "3:41") for correct reading.

## Project layout

```
voice studio/
├── studio.py        # the browser app
├── studio.bat       # double-click to launch
├── generate.py      # command-line version
├── voiceover.bat    # command-line launcher
├── clean_refs.py    # utility: noise-clean voice references
├── voices/          # voice library (.wav references, 10-20s each)
├── scripts/         # your voiceover scripts (.txt)
└── output/          # generated MP3s and clips
```

## Credits

- TTS engine: [Chatterbox](https://github.com/resemble-ai/chatterbox) by Resemble AI (MIT license)
- Included voice references: cut from [LibriVox](https://librivox.org/) public-domain audiobook recordings
- UI: [Gradio](https://gradio.app/)

## License

MIT — do whatever you want, including commercial YouTube content. See [LICENSE](LICENSE).
