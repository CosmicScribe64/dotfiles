# Agent Instructions

## Repository purpose

This is a dotfiles repository. It stores personal configuration files and AI agent skills, and provides a `setup.sh` script to install them into `$HOME` via symlinks (or copies).

## Critical rule: setup.sh must stay in sync

**Whenever a new config file or directory is added to this repo that should be installed into `$HOME`, you must update `setup.sh`.**

Specifically, add an `install_item` call in the `# --- Items to install ---` section:

```bash
install_item "$REPO_DIR/<repo-path>" "$HOME_DIR/<home-path>"
```

Also update the contents table in `README.md`.

Failure to do this means the new config will exist in the repo but never be installed on a fresh setup.

## Structure

```
.
├── .copilot/
│   ├── instructions/      # installed to ~/.copilot/instructions
│   └── skills/            # installed to ~/.copilot/skills
│       └── ...            # first-party and ignored local skills
├── .mattpocock.skills/    # submodule; engineering/ and productivity/ skills installed to ~/.copilot/skills
├── .bashrc                # installed to ~/.bashrc
├── .vimrc                 # installed to ~/.vimrc
├── setup.sh               # install script
├── README.md
└── AGENTS.md              # this file
```

## setup.sh behavior

- Updates the `.mattpocock.skills` submodule to upstream `main` (warns and continues if offline or if the submodule has local edits), then installs configuration and skills from this checkout
- Prunes stale skills from `~/.copilot/skills` against every skill source, including the submodule buckets
- Symlinks by default; `--copy` resolves symlinks and copies real files (useful for isolated environments)
- Idempotent in symlink mode: already-correct symlinks are skipped without prompting
- Prompts before overwriting anything that exists but is wrong
- Prunes stale skill symlinks left over from renamed/removed upstream skills, both inside the repo (`.copilot/skills/`) and in `~/.copilot/skills/`
