# dotfiles

Personal Bash, tmux, Vim, and Copilot configuration, installed into `$HOME`.

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
[mattpocock/skills](https://github.com/mattpocock/skills) and
[wheresryan22/anatomy](https://github.com/wheresryan22/anatomy) submodules to the
latest upstream `main`. Commit the submodule pointers when they change. Setup does not
fetch other dependencies.

```bash
./setup.sh --copy   # Copy files instead of linking
./setup.sh -y       # Approve all overwrites and removals without prompting
./setup.sh --help   # Show options
```

## Contents

| Source | Installed location |
| --- | --- |
| [.bashrc](.bashrc), [.tmux.conf](.tmux.conf), [.vimrc](.vimrc) | Matching files in `$HOME` |
| [.cows/custom-cows/](.cows/custom-cows/) | `~/.cows/custom-cows/` |
| [.copilot/instructions/](.copilot/instructions/) | `~/.copilot/instructions/` |
| [.copilot/skills/](.copilot/skills/) | `~/.copilot/skills/` |
| [.mattpocock.skills/](.mattpocock.skills/) `skills/engineering/` and `skills/productivity/` | `~/.copilot/skills/` |
| [.wheresryan22.anatomy/](.wheresryan22.anatomy/) | `~/.copilot/skills/anatomy/` |

### Bundled Skills

| Skill | Purpose |
| --- | --- |
| [copy-editor](.copilot/skills/copy-editor/) | Local writing workbench with diagnostic reviews and fresh-agent version comparisons. You write; agents review without rewriting. |
| [demo](.copilot/skills/demo/) | Capture real evidence and build a feature demonstration. |
| [deslop](.copilot/skills/deslop/) | Draft, rewrite, or audit prose; optionally apply its plain-language style to answers and explanations. Includes `scripts/find_tells.py`, which lists likely AI-writing tells for review. Simplify code only when explicitly requested. |
| [test-suite-auditor](.copilot/skills/test-suite-auditor/) | Find weak assertions, missing coverage, and flaky tests. |

## Adding Configuration

Add the file, add an `install_item` entry in [setup.sh](setup.sh), and update this
README. Copilot skills and instructions are discovered automatically, so new
items in those directories need no installer change.
