"""Clean voice reference files: noise-reduce, trim silence, normalize.
Run this after adding a noisy voice recording to voices/.
Originals are kept in voices/raw/ the first time this runs.
"""
import shutil
from pathlib import Path

import librosa
import noisereduce as nr
import numpy as np
import soundfile as sf

vdir = Path(__file__).resolve().parent / "voices"
raw = vdir / "raw"
raw.mkdir(exist_ok=True)

for f in sorted(vdir.glob("*.wav")):
    backup = raw / f.name
    if not backup.exists():
        shutil.copy2(f, backup)
    y, sr = librosa.load(backup, sr=24000, mono=True)
    y = nr.reduce_noise(y=y, sr=sr, stationary=True, prop_decrease=0.85)
    y, _ = librosa.effects.trim(y, top_db=35)
    peak = np.abs(y).max()
    if peak > 0:
        y = y / peak * 0.9
    sf.write(f, y, sr)
    print(f"cleaned {f.name}  {len(y)/sr:.1f}s")
print("done")
