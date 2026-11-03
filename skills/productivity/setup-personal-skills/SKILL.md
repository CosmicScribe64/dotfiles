---
name: setup-personal-skills
description: "Install or update my skills: this dotfiles repo's skills plus mattpocock/skills and i-have-adhd. Use when asked to install, update, or sync my skills."
disable-model-invocation: true
---

# Setup personal skills

Install copies, never symlinks, so installed skills keep working when a checkout moves or changes.

1. Pick the target: `~/.copilot/skills/` unless the user names another skills directory.
2. Gather the sources into a fresh temp directory:
   - This repo: the checkout the user points at (default `~/Repos/dotfiles`), else clone `https://github.com/CosmicScribe64/dotfiles`. Take every skill folder under `skills/engineering/`, `skills/productivity/`, and `skills/personal/`. `personal/` is gitignored and exists only on machines that have it.
   - `https://github.com/mattpocock/skills`: every skill folder under `skills/engineering/` and `skills/productivity/`.
   - `https://github.com/ayghri/i-have-adhd`: `skills/i-have-adhd/`.
3. If two sources ship a skill with the same name, stop and ask which wins.
4. Replace each target skill folder with its source folder as a whole, so deleted files go too. Skip `__pycache__/`.
5. List installed skills that no source provides. Ask before removing any; the user may keep others there.
6. Check `diff -r` between every source folder and its installed copy is clean, then report skills added, updated, unchanged, and left alone.
