# dotfiles

My Bash, Vim, and agent skill configuration.

## Install

Copy [.bashrc](.bashrc), [.vimrc](.vimrc), and [.cows/](.cows/) into `$HOME`.

For skills, point an agent at this repo and ask it to install or update them. The [setup-personal-skills](skills/productivity/setup-personal-skills/) skill describes the steps: it copies these skills, [mattpocock/skills](https://github.com/mattpocock/skills), and [ayghri/i-have-adhd](https://github.com/ayghri/i-have-adhd) into `~/.copilot/skills/`.

## Skills

Skills are grouped in bucket folders, following [mattpocock/skills](https://github.com/mattpocock/skills). `skills/personal/` is gitignored for skills that stay on my machines.

### Engineering

| Skill | Purpose |
| --- | --- |
| [adversarial-review](skills/engineering/adversarial-review/) | Fresh subagents try to break a change: trace each changed value through unchanged producers and consumers, sweep a defect-class checklist, prove findings by running code, and re-review every push. |
| [change-walkthrough](skills/engineering/change-walkthrough/) | Explain a PR, branch, or diff as a plain story with the changed code quoted beside each idea. `scripts/check_quotes.py` checks every quote against the head commit and the diff. |
| [check-overengineering](skills/engineering/check-overengineering/) | Keep a change to the smallest complete diff, or flag overbuilt parts of a plan or diff. |
| [cpp-style](skills/engineering/cpp-style/) | My C++ naming, constant, and header-doc conventions. |
| [pr-workflow](skills/engineering/pr-workflow/) | Pre-commit checks, PR description format, and stacked PRs. |
| [requirement-map](skills/engineering/requirement-map/) | Map every added and removed line of a diff to a requirement and reconcile totals against `git diff --numstat`. |
| [test-suite-auditor](skills/engineering/test-suite-auditor/) | Find weak assertions, missing coverage, and flaky tests. |
| [verification-status](skills/engineering/verification-status/) | Table each claim made, whether it is verified, and the evidence. |

### Productivity

| Skill | Purpose |
| --- | --- |
| [deslop](skills/productivity/deslop/) | Draft, rewrite, or audit prose in a plain, human style. `scripts/find_tells.py` lists likely AI-writing tells for review. |
| [llm-wiki](skills/productivity/llm-wiki/) | Set up a project wiki with a Kanban ticket board. |
| [setup-personal-skills](skills/productivity/setup-personal-skills/) | Install or update all of the above plus the external skill sets. |
