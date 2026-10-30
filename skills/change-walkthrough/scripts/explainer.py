"""Base scene for a voiced change-walkthrough explainer. Copy next to scene.py and subclass Explainer."""
import json
import wave

from manim import *

BG = "#0f1117"
MONO = "DejaVu Sans Mono"


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
    def setup(self):
        self.camera.background_color = BG
        self.title_m = None
        self.cap_m = None
        self._voice_end = 0.0
        self.cues = []

    def sync(self):
        """Wait until the current narration beat has finished."""
        left = self._voice_end - self.renderer.time
        if left > 0.01:
            self.wait(left)

    def say(self, key):
        """Wait for the previous beat, then start narration/<key>.wav."""
        self.sync()
        path = f"narration/{key}.wav"
        with wave.open(path) as w:
            duration = w.getnframes() / w.getframerate()
        self.add_sound(path)
        self._voice_end = self.renderer.time + duration + 0.25
        # captions.py turns this log into subtitles.
        self.cues.append([key, self.renderer.time, duration])
        with open("cues.json", "w") as f:
            json.dump(self.cues, f)

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
        """Fade out everything except the title and caption."""
        keep = [m for m in (self.title_m, self.cap_m) if m is not None]
        body = [m for m in self.mobjects if m not in keep]
        if body:
            self.play(*[FadeOut(m) for m in body], run_time=0.6)
