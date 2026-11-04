"""Base scene for a voiced change-walkthrough explainer. Copy next to scene.py and subclass Explainer.

List the section methods in SECTIONS. render.py renders each section as its own scene (env SECTION) in parallel.
STILLS=1 with `manim -s` saves a PNG of the stage before every beat and section end into stills/, for layout checks.
"""
import json
import os
import re
import wave

from manim import *

BG = "#0f1117"
MONO = "DejaVu Sans Mono"

_say_path = "narration/say.json"
_SAY = json.load(open(_say_path)) if os.path.exists(_say_path) else {}
_SAY_RE = re.compile(
    r"(?<!\w)(" + "|".join(re.escape(k) for k in sorted(_SAY, key=len, reverse=True)) + r")(?!\w)") if _SAY else None


def spoken(text):
    """The text as the voice says it, so phrase positions follow the audio rather than the written digits."""
    text = " ".join(text.split())
    return _SAY_RE.sub(lambda m: _SAY[m[1]], text) if _SAY_RE else text


def tx(s, size=28, color=WHITE, mono=False, **kw):
    return Text(s, font_size=size, color=color, font=MONO if mono else "", **kw)


def fit(m, width):
    if m.width > width:
        m.scale_to_fit_width(width)
    return m


def baseline(text_mobject):
    """Text built as tx("word|"): hides the "|", whose ascender-to-descender box puts centred words on one baseline."""
    text_mobject[-1].set_opacity(0)
    return text_mobject


class Explainer(Scene):
    SECTIONS = []  # method names in order, e.g. ["s1_title", "s2_problem"]; the prefix before "_" names the section

    def setup(self):
        self.camera.background_color = BG
        self.title_m = None
        self.cap_m = None
        self._voice_end = 0.0
        self._beat = ""
        self._t0 = 0.0
        self._dur = 0.0
        self.cues = []
        self.cues_path = os.environ.get("CUES", "cues.json")
        self.stills = bool(os.environ.get("STILLS"))

    def construct(self):
        only = os.environ.get("SECTION")
        for name in self.SECTIONS:
            if only is None or name.split("_")[0] == only:
                getattr(self, name)()
        if only:
            self.sync()
            self.still(f"{only}_end")
            if self.mobjects:
                self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.4)

    def still(self, name):
        if self.stills:
            os.makedirs("stills", exist_ok=True)
            self.renderer.update_frame(self, ignore_skipping=True)
            self.camera.get_image().save(f"stills/{name}.png")

    def sync(self):
        """Wait until the current narration beat has finished."""
        left = self._voice_end - self.renderer.time
        if left > 0.01:
            self.wait(left)

    def say(self, key):
        """Wait for the previous beat, then start narration/<key>.wav."""
        self.sync()
        self.still(key)
        path = f"narration/{key}.wav"
        with wave.open(path) as w:
            duration = w.getnframes() / w.getframerate()
        # Scene.add_sound drops the clip while skip_animations is still set from a cached play(); write directly.
        if not self.renderer._original_skipping_status:
            self.renderer.file_writer.add_sound(path, self.renderer.time)
        self._voice_end = self.renderer.time + duration + 0.25
        section, k = key.rsplit("_", 1)
        paragraphs = [p for p in open(f"narration/{section}.txt").read().split("\n\n") if p.strip()]
        self._beat, self._t0, self._dur = spoken(paragraphs[int(k)]), self.renderer.time, duration
        # captions.py turns this log into subtitles.
        self.cues.append([key, self.renderer.time, duration])
        with open(self.cues_path, "w") as f:
            json.dump(self.cues, f)

    def when(self, phrase, lead=0.0):
        """Wait until roughly when `phrase` is spoken in the current beat (proportional to characters)."""
        target = self._t0 + self._dur * self._beat.index(spoken(phrase)) / len(self._beat) + lead
        left = target - self.renderer.time
        if left > 0.01:
            self.wait(left)

    def ttl(self, s):
        new = fit(tx(s, 42), 12.5).to_edge(UP, buff=0.4)
        if self.title_m is None:
            self.play(FadeIn(new, shift=DOWN * 0.2), run_time=0.6)
        else:
            self.play(FadeTransform(self.title_m, new), run_time=0.6)
        self.title_m = new

    def cap(self, s, wait=0.0):
        new = fit(tx(s, 30, GREY_A), 12.8).to_edge(DOWN, buff=0.45)
        if self.cap_m is None:
            self.play(FadeIn(new, shift=UP * 0.2), run_time=0.5)
        else:
            self.play(FadeTransform(self.cap_m, new), run_time=0.5)
        self.cap_m = new
        if wait:
            self.wait(wait)

    def clear_body(self):
        """Wait for the beat, then fade out everything except the title and caption."""
        self.sync()
        keep = [m for m in (self.title_m, self.cap_m) if m is not None]
        body = [m for m in self.mobjects if m not in keep]
        self.still(f"{self.cues[-1][0]}_end" if self.cues else "clear")
        if body:
            self.play(*[FadeOut(m) for m in body], run_time=0.6)
