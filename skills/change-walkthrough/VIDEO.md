# Explainer video (optional)

A 3Blue1Brown-style animated explainer of the walkthrough's story, voiced. Make one when the reader says yes to the offer at the end of the walkthrough, or asks for one. It needs the finished walkthrough: the story is the script, and every number on screen comes from it.

## Steps

1. **Plan the sections.** One section per part of the story, in the same order: a title, the problem, one section per part, the bugs found along the way, and an outro naming what comes next. For each, pick one visual that carries the idea (dots thinning on a time axis, two boxes linked by an arrow, a bar counting to a percentage, a geometry diagram with its formula), and one caption per beat. Done when every part of the story has a section, and every number you plan to show is in the walkthrough.

2. **Write the narration**, one file per section: `narration/s1.txt`, `s2.txt`, ... Each paragraph is one beat and becomes one clip, spoken while its caption shows. Talk like the story: plain words, the real numbers, paths and IDs said naturally ("the detections file"). Write it as a reader would read it, because the same text becomes the subtitles; put how the voice should say awkward pieces in `narration/say.json` (`{"VSI-4675": "V S I four six seven five", "35%": "thirty-five percent"}`). Mark made-up values as examples ("say the camera is panned 40°"). Aim for 2.5 to 3.5 minutes in total; narration sets the length, since the visuals wait for the voice.

3. **Generate the voice locally.** The narration describes internal code, so it stays on this machine: run the TTS model in Docker and bind it to localhost.

   ```
   docker run -d --rm --name kokoro-tts -p 127.0.0.1:8880:8880 ghcr.io/remsky/kokoro-fastapi-cpu:latest
   python3 <this skill's folder>/scripts/narrate.py narration
   docker stop kokoro-tts
   ```

   `narrate.py` writes `sN_k.wav` per paragraph and skips clips that exist; pass `--force` after editing text. Done when every paragraph has a clip.

4. **Write the scene.** Copy `scripts/explainer.py` next to `scene.py` and subclass `Explainer`: `ttl()` sets the title, `cap()` the caption, `clear_body()` empties the stage, and `say("s3_1")` waits for the previous beat to finish and then starts the next clip, so the animation never cuts off the voice. Call `say()` just before the visual it describes; call `sync()` before clearing a section. Use `MathTex` for formulas. Keep text at font size 22 or more, and build column labels as `baseline(tx("word|"))` so different words share a baseline.

5. **Render in Docker**, detached, because a 1080p render takes several minutes and a shared terminal can kill it:

   ```
   (setsid nohup bash -c 'docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/manim manimcommunity/manim:stable manim -qh scene.py <Scene> -o video.mp4 > render.log 2>&1; echo $? > render.done' > /dev/null 2>&1 < /dev/null &)
   ```

   Iterate at `-ql`. `-qh` writes to `media/videos/scene/1080p60/`; copy the result to one handoff path.

6. **Add subtitles.** `say()` logs each clip's start to `cues.json`. Build the subtitles and add them as a track the viewer can switch on:

   ```
   python3 <this skill's folder>/scripts/captions.py cues.json narration video.srt
   ffmpeg -i video.mp4 -i video.srt -map 0 -map 1 -c copy -c:s mov_text -metadata:s:s:0 language=eng video_cc.mp4
   ```

   Hand off the `.srt` beside the video as well, for players and sites that take a separate file.

7. **Review it before handing off.** The visuals and their facts get the same scrutiny as the walkthrough's quotes.
   - Contact sheets, one frame every 4 seconds: `ffmpeg -i video.mp4 -vf "fps=1/4,scale=640:-1,tile=3x5" ...`. Check that nothing overlaps or runs off screen, and that captions are readable. `view_image` caches by path, so give every extracted image a new name.
   - Each visual says what the code does. Check reference frames and directions (bow or north), what a step removes (per frame or overall), and every number against the walkthrough.
   - Sync: for three or four beats that name a number, compute when it is spoken and look at that frame; the number should be on screen.
   - Audio: `ffprobe` shows an audio stream; `ffmpeg -af volumedetect` is not silent; `silencedetect=noise=-40dB:d=2.5` lists only gaps you meant.
   - Subtitles: `ffprobe` shows a `mov_text` stream, and a frame rendered with `-vf subtitles=video.srt` shows readable text matching the narration at that moment.

   Done when every finding is fixed and re-rendered. Hand off the path, the duration, what you checked, and that you could not listen to it.
