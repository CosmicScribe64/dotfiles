# Explainer video (optional)

A 3Blue1Brown-style animated explainer of the walkthrough's story, voiced. Make one when the reader says yes to the offer at the end of the walkthrough, or asks for one. It needs the finished walkthrough: the story is the script, and every number on screen comes from it.

## Steps

1. **Plan the sections.** One section per part of the story, in the same order: a title, the problem, one section per part, the bugs found along the way, and an outro naming what comes next. For each, pick one visual that carries the idea (dots thinning on a time axis, two boxes linked by an arrow, a bar counting to a percentage, a geometry diagram with its formula), and one caption per beat. Done when every part of the story has a section, and every number you plan to show is in the walkthrough or marked as an example.

2. **Write the narration**, one file per section: `narration/s1.txt`, `s2.txt`, ... Each paragraph is one beat and becomes one clip, spoken while its caption shows. Talk like the story: plain words, the real numbers, paths and IDs said naturally ("the detections file"). Write it as a reader would read it, because the same text becomes the subtitles; put how the voice should say awkward pieces in `narration/say.json` (`{"VSI-4675": "V S I four six seven five", "35%": "thirty-five percent"}`). Mark made-up values as examples ("say the camera is panned 40°"). Aim for 2.5 to 3.5 minutes in total; narration sets the length, since the visuals wait for the voice.

3. **Generate the voice locally.** The narration describes internal code, so it stays on this machine: run the TTS model in Docker and bind it to localhost. Both images are pinned to the digests last verified with these scripts.

   ```
   docker run -d --rm --name kokoro-tts -p 127.0.0.1:8880:8880 ghcr.io/remsky/kokoro-fastapi-cpu@sha256:cbcc28802fb5d1eaaba8b91e38b0e872a669e85831c513cf6a29c709cbe25405
   python3 <this skill's folder>/scripts/narrate.py narration; docker stop kokoro-tts
   ```

   `narrate.py` waits for the server, writes `sN_k.wav` per paragraph, and skips clips whose text hasn't changed. Done when every paragraph has a clip.

4. **Write the scene.** Copy `scripts/explainer.py` and `scripts/render.py` next to `scene.py` and subclass `Explainer`. List the section methods in order in `SECTIONS = ["s1_title", "s2_problem", ...]`; the prefix before `_` must match the narration file, and every section must call `say()` at least once. `ttl()` sets the title, `cap()` the caption, `clear_body()` waits for the beat and empties the stage, `say("s3_1")` waits for the previous beat to finish and then starts the next clip, and `when("phrase")` waits until roughly when that phrase is spoken in the current beat. Call `say()` just before the visual it describes, and `when()` to show a number as it is said. Each section renders as its own scene, so it starts on an empty stage and must not rely on objects from an earlier section. Use `MathTex` for formulas. Keep text at font size 22 or more, and build column labels as `baseline(tx("word|"))` so different words share a baseline.

   Check layout with stills, not videos. This takes about 20 seconds and writes `stills/<beat>.png` (the stage as each beat starts) and `stills/<beat>_end.png` (before each clear):

   ```
   docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/manim -e STILLS=1 -e CUES=/tmp/cues.json manimcommunity/manim@sha256:af29da8765a26ab1f9f1d61d401e95d50520753634ed8e343fd5c05283a459e7 manim -ql -s --media_dir /tmp/media scene.py <Scene>
   ```

   Fix overlaps and off-screen text from the stills before rendering video. `view_image` caches by path, so move or rename `stills/` between rounds.

5. **Render** with `python3 render.py <Scene>`, detached, so a shared terminal can't kill it. It renders every section in its own Docker container in parallel at 1080p30, joins them into `video.mp4` and writes `cues.json` with each clip's time in the joined video. The PR 6 video (11 sections, 238 s) took 42 seconds.

   ```
   (setsid nohup bash -c 'python3 render.py <Scene> > render.log 2>&1; echo $? > render.done' > /dev/null 2>&1 < /dev/null &)
   tail --pid=$(pgrep -f "render.py <Scene>" | head -1) -f /dev/null; cat render.done render.log
   ```

   The second line blocks until the render exits, without polling. After a fix, `--only s3,s7` re-renders just those sections and rejoins the rest. A failing section's log is `sections/<section>.log`. The agent that started a render waits for it and runs the remaining steps; don't hand a render in progress to a subagent.

6. **Add subtitles.** Build the subtitles from `cues.json` and add them as a track the viewer can switch on:

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
