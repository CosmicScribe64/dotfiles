#!/usr/bin/env python3
"""Turn narration/sN.txt into narration/sN_k.wav, one clip per paragraph, via a local Kokoro server.

Usage: python3 narrate.py <narration dir> [--force]
Env: VOICE (default af_heart), SPEED (default 1.1), TTS_URL (default http://127.0.0.1:8880).
Optional <narration dir>/say.json maps written text to how the voice should say it
({"VSI-4675": "V S I four six seven five"}), so the .txt files stay readable as captions.
"""
import glob
import json
import os
import re
import sys
import urllib.request
import wave

folder = sys.argv[1]
voice = os.environ.get("VOICE", "af_heart")
speed = float(os.environ.get("SPEED", "1.1"))
url = os.environ.get("TTS_URL", "http://127.0.0.1:8880") + "/v1/audio/speech"
say_path = os.path.join(folder, "say.json")
say = json.load(open(say_path)) if os.path.exists(say_path) else {}


def spoken(text):
    text = " ".join(text.split())
    for written in sorted(say, key=len, reverse=True):
        text = re.sub(r"(?<!\w)" + re.escape(written) + r"(?!\w)", say[written], text)
    return text


for txt in sorted(glob.glob(os.path.join(folder, "s[0-9]*.txt"))):
    section = os.path.basename(txt)[:-4]
    beats = [b.strip() for b in open(txt).read().split("\n\n") if b.strip()]
    for k, text in enumerate(beats):
        out = os.path.join(folder, f"{section}_{k}.wav")
        if os.path.exists(out) and "--force" not in sys.argv:
            continue
        body = {"model": "kokoro", "input": spoken(text), "voice": voice, "response_format": "wav", "speed": speed}
        request = urllib.request.Request(
            url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=300) as response:
            raw = response.read()
        # Kokoro streams WAV with an unknown-length header, which Python's wave module misreads.
        pcm = raw[raw.index(b"data") + 8:]
        with wave.open(out, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(24000)
            w.writeframes(pcm)
        print(out, flush=True)
