---
name: setup-personal-skills
description: "Install or update my skills for whichever agent is running: this dotfiles repo's skills plus mattpocock/skills and i-have-adhd. Use when asked to install, update, or sync my skills."
disable-model-invocation: true
---

# Setup personal skills

1. Find the skills directory for the agent you are: its user-level (global) skills directory, such as `~/.copilot/skills/`, `~/.claude/skills/`, or `~/.agents/skills/`. Use the user's choice if they name one; ask if you can't tell.
2. Install the external skill sets by their own instructions, for this agent. Each upstream keeps its install steps current, including plugin installs that update themselves:
   - mattpocock/skills: step 1 under "Installation" in `https://github.com/mattpocock/skills/blob/main/README.md`. Skip step 2: `setup-matt-pocock-skills` configures one repo at a time, so the user runs it per project.
   - i-have-adhd: `https://github.com/ayghri/i-have-adhd/blob/main/AGENTS.md`.
3. Copy this repo's skills into the skills directory as plain copies, never symlinks. The source is the checkout the user points at (default `~/Repos/dotfiles`), else a fresh clone of `https://github.com/CosmicScribe64/dotfiles`. Take every folder with a `SKILL.md` under `skills/engineering/`, `skills/productivity/`, and `skills/personal/`; `personal/` is gitignored and exists only on machines that have it. Replace each installed folder as a whole so deleted files go too, and skip `__pycache__/`.
4. If two sources provide a skill with the same name, stop and ask which wins. This includes plugin-installed skills.
5. List skills in the directory that no source provides, including copies left from an earlier install that a plugin now supplies. Ask before removing any; the user may keep others there.
6. Check `diff -r` between each of this repo's skill folders and its installed copy is clean. Report what each upstream installer did, and which of this repo's skills were added, updated, unchanged, or left alone.
