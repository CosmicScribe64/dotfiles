# dotfiles

Personal Bash, Vim, and Copilot configuration, installed into `$HOME`.

## Install

```bash
git clone https://github.com/CosmicScribe64/dotfiles.git
cd dotfiles
./setup.sh
```

[setup.sh](setup.sh) creates symlinks by default and skips existing correct links.
It prompts before overwriting files or removing installed Copilot skills and
instructions absent from this checkout. Review those prompts if you keep other
skills locally. Setup also updates the
[mattpocock/skills](https://github.com/mattpocock/skills) submodule to the
latest upstream `main`. Commit the submodule pointer when it changes. Setup does not
fetch other dependencies.

```bash
./setup.sh --copy   # Copy files instead of linking
./setup.sh -y       # Approve all overwrites and removals without prompting
./setup.sh --help   # Show options
```

## Contents

| Source | Installed location |
| --- | --- |
| [.bashrc](.bashrc), [.vimrc](.vimrc) | Matching files in `$HOME` |
| [.cows/custom-cows/](.cows/custom-cows/) | `~/.cows/custom-cows/` |
| [.copilot/instructions/](.copilot/instructions/) | `~/.copilot/instructions/` |
| [skills/](skills/) (linked at `.copilot/skills`) | `~/.copilot/skills/` |
| [.mattpocock.skills/](.mattpocock.skills/) `skills/engineering/` and `skills/productivity/` | `~/.copilot/skills/` |

### Bundled Skills

| Skill | Purpose |
| --- | --- |
| [deslop](skills/deslop/) | Draft, rewrite, or audit prose; optionally apply its plain-language style to answers and explanations. Includes `scripts/find_tells.py`, which lists likely AI-writing tells for review. Simplify code only when explicitly requested. |
| [llm-wiki](skills/llm-wiki/) | Set up a project wiki with a Kanban ticket board. |
| [org-braindump](skills/org-braindump/) | Organize a loose braindump into a summary, grouped notes, next actions, and open questions. |
| [project-setup](skills/project-setup/) | Set up a repository with an orchestrator workflow, Dockerized tooling, an LLM wiki ticket board, and Matt Pocock skills. |
| [test-suite-auditor](skills/test-suite-auditor/) | Find weak assertions, missing coverage, and flaky tests. |
| [verification-status](skills/verification-status/) | List each claim made, whether it is verified, and the supporting evidence in a table. |

## Adding Configuration

Add the file, add an `install_item` entry in [setup.sh](setup.sh), and update this
README. Copilot skills and instructions are discovered automatically, so new
items in those directories need no installer change.
