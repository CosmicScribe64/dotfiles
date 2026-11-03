---
name: setup-personal-skills
description: "Install or update my skills for whichever agent is running: this dotfiles repo's skills plus mattpocock/skills and i-have-adhd. Use when asked to install, update, or sync my skills."
disable-model-invocation: true
---

# Setup personal skills

Install everything globally (for all projects), never into the current project.

1. Pick one user-level skills directory for the running agent, such as `~/.copilot/skills/`, `~/.claude/skills/`, or `~/.agents/skills/`, or the one the user names. Some agents scan several of these, so a skill in two of them shows up twice. Ask if you can't tell.
2. Install the external skill sets with their own instructions for this agent, choosing the global option (for `npx skills`, that's `-g`):
   - mattpocock/skills: step 1 under "Installation" in `https://github.com/mattpocock/skills/blob/main/README.md`. Skip its step 2: `setup-matt-pocock-skills` configures one repo, so the user runs it per project.
   - i-have-adhd: this agent's section of `https://github.com/ayghri/i-have-adhd/blob/main/INSTALL.md`. Skip its optional always-on block.

   If a step needs something you can't do, such as a UI command, give the user that step and wait.
3. Copy this repo's skills into the directory from step 1, as plain copies and never symlinks. The source is the checkout the user points at (default `~/Repos/dotfiles`), else a fresh clone of `https://github.com/CosmicScribe64/dotfiles`. Take every folder with a `SKILL.md` under `skills/engineering/`, `skills/productivity/`, and `skills/personal/`; `personal/` is gitignored and exists only on machines that have it. Replace each installed folder whole so deleted files go too, and skip `__pycache__/`.
4. If two sources provide a skill with the same name, stop and ask which wins. Plugins don't put files in the directory, so check their skill lists too.
5. List skills in the directory that no source provides, including copies from an earlier install that a plugin now supplies. Ask before removing any; the user may keep others there.
6. Check that `diff -r -x __pycache__` between each of this repo's skill folders and its installed copy is empty. Report what each upstream installer did, and which of this repo's skills were added, updated, unchanged, or left alone. Tell the user to start a new chat so the agent loads the new skills.
