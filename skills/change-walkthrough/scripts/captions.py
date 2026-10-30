#!/usr/bin/env python3
"""Write subtitles for a voiced explainer from the render's cue log and the narration text.

Usage: python3 captions.py <cues.json> <narration dir> <out.srt>
cues.json is [[key, start_s, duration_s], ...] as Explainer.say() logs it; key "s3_1" is paragraph 1 of s3.txt.
Each paragraph is split into sentences, timed in proportion to their length.
"""
import json
import os
import re
import sys
import textwrap

cues_path, folder, out_path = sys.argv[1:4]
MAX_CHARS = 84  # two lines of 42


def stamp(seconds):
    ms = round(seconds * 1000)
    return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"


def chunks(paragraph):
    for sentence in re.split(r"(?<=[.!?])\s+", " ".join(paragraph.split())):
        yield from textwrap.wrap(sentence, MAX_CHARS)


paragraphs = {}
entries = []
for key, start, duration in json.load(open(cues_path)):
    section, beat = key.rsplit("_", 1)
    if section not in paragraphs:
        text = open(os.path.join(folder, f"{section}.txt")).read()
        paragraphs[section] = [p for p in text.split("\n\n") if p.strip()]
    parts = list(chunks(paragraphs[section][int(beat)]))
    total = sum(len(p) for p in parts)
    t = start
    for part in parts:
        length = duration * len(part) / total
        entries.append((t, t + length, "\n".join(textwrap.wrap(part, 42))))
        t += length

with open(out_path, "w") as out:
    for index, (begin, end, text) in enumerate(entries, 1):
        out.write(f"{index}\n{stamp(begin)} --> {stamp(end)}\n{text}\n\n")
print(f"{len(entries)} subtitles -> {out_path}")
