#!/usr/bin/env python3
"""Render each section of an Explainer scene in its own Docker container, in parallel, and join them.

Usage (from the folder holding scene.py): python3 render.py <SceneClass> [--fps 30] [--quality h] [--jobs N] [--only s3,s7]
Writes video.mp4 and cues.json there. Each section keeps its own Manim cache (media/<section>/), so after a fix
only sections whose code or narration changed take long; --only re-renders just those and rejoins the rest.
"""
import argparse
import ast
import concurrent.futures
import json
import os
import subprocess
import sys
import time

IMAGE = "manimcommunity/manim@sha256:af29da8765a26ab1f9f1d61d401e95d50520753634ed8e343fd5c05283a459e7"

ap = argparse.ArgumentParser()
ap.add_argument("scene")
ap.add_argument("--fps", default="30")
ap.add_argument("--quality", default="h", choices="lmhpk")
ap.add_argument("--jobs", type=int, default=os.cpu_count() // 2 or 1)
ap.add_argument("--only", help="comma-separated sections to re-render; the others are reused")
args = ap.parse_args()

# Manim isn't installed on the host, so read SECTIONS from the source instead of importing scene.py.
scene_class = next(n for n in ast.parse(open("scene.py").read()).body
                   if isinstance(n, ast.ClassDef) and n.name == args.scene)
listing = next(ast.literal_eval(s.value) for s in scene_class.body
               if isinstance(s, ast.Assign) and getattr(s.targets[0], "id", "") == "SECTIONS")
sections = [name.split("_")[0] for name in listing]
todo = args.only.split(",") if args.only else sections
os.makedirs("sections", exist_ok=True)
uid = f"{os.getuid()}:{os.getgid()}"


def render(section):
    cmd = ["docker", "run", "--rm", "--user", uid, "-v", f"{os.getcwd()}:/manim",
           "-e", f"SECTION={section}", "-e", f"CUES=sections/{section}.json", IMAGE,
           "manim", f"-q{args.quality}", "--fps", args.fps, "--media_dir", f"media/{section}",
           "-o", f"{section}.mp4", "scene.py", args.scene]
    start = time.time()
    with open(f"sections/{section}.log", "w") as log:
        code = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT).returncode
    return section, code, time.time() - start


failed = []
with concurrent.futures.ThreadPoolExecutor(args.jobs) as pool:
    for section, code, took in pool.map(render, todo):
        print(f"{section}: exit {code}, {took:.0f} s", flush=True)
        if code:
            failed.append(section)
if failed:
    sys.exit(f"failed: {failed}; see sections/<section>.log")


def section_mp4(section):
    found = [os.path.join(root, f"{section}.mp4") for root, _, files in os.walk(f"media/{section}/videos")
             if f"{section}.mp4" in files and "partial_movie_files" not in root]
    return max(found, key=os.path.getmtime)


def duration(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                                capture_output=True, text=True, check=True).stdout)


parts, cues, offset = [], [], 0.0
for section in sections:
    path = section_mp4(section)
    if not os.path.exists(f"sections/{section}.json"):
        sys.exit(f"{section} has no narration; concat needs an audio stream in every section")
    parts.append(path)
    cues += [[key, start + offset, dur] for key, start, dur in json.load(open(f"sections/{section}.json"))]
    offset += duration(path)

with open("sections/list.txt", "w") as f:
    f.writelines(f"file '{os.path.abspath(p)}'\n" for p in parts)
# Re-encode audio so AAC priming at each joint doesn't drift the voice against the cues.
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "sections/list.txt",
                "-c:v", "copy", "-c:a", "aac", "video.mp4"], check=True)
json.dump(cues, open("cues.json", "w"))
print(f"video.mp4: {duration('video.mp4'):.1f} s, {len(parts)} sections, {len(cues)} cues")
