# Copy Editor

A local writing workbench and agent skill. You write; the agent diagnoses problems
without rewriting or praise. Includes 30 editing checks, passage-linked findings,
saved drafts, and A/B comparisons. No built-in model runner.

## Start

Requires **Python 3.10+ and a browser** on macOS/Linux. No pip packages, Node,
model CLI, or build step. Install through the [dotfiles setup](../../../README.md),
then run:

```bash
python3 "$HOME/.copilot/skills/copy-editor/scripts/workshop.py" serve --open
```

Keep the terminal running and use the printed `127.0.0.1` URL. Stop and restart
the server when updating the skill; reloading the page alone does not update Python.
Keep the same data directory across upgrades. Older database formats are backed up
before migration; do not reopen an upgraded database with v2/v3.

## Write, Review, Compare

1. **Write:** create a blank document or import text/Markdown. An agent can open
  a PR template unchanged and wait while you fill it in. `--file PATH` imports
  a new copy each time, so omit it when reopening saved work.
2. **Review:** choose a check under **All passes**, then **Review externally**.
  **Copy agent prompt** lets a local agent review and import findings directly.
  For a remote chat, copy or export the packet and import its returned JSON.
3. **Revise:** inspect linked findings and make your own edits. Nothing rewrites
  your draft automatically. Resolve or decline findings as you decide.
4. **Compare:** select an earlier snapshot and **Current working draft** under
  **Compare versions**. Copy the agent prompt to delegate to a fresh subagent
  and import its result locally, or export the packet for a new chat.

Comparison context and criteria are optional. Copy and Export capture the current
draft and reuse an unfinished comparison when snapshots and context are unchanged,
preserving its number and A/B order. Changed inputs or a completed result start a
new comparison. Fresh subagents are assumed isolated unless their tool says they
inherit history; an import does not prove independence.

Reviews stay attached to their snapshots. A checklist mark means a review ran on
matching text, audience, purpose, and pass instructions, not that every issue is
resolved. Editing can make checks stale; rerun only what helps.

## Storage and Privacy

- **Linux:** `${XDG_DATA_HOME:-~/.local/share}/voice-preserving-copyeditor/`
- **macOS:** `~/Library/Application Support/VoicePreservingCopyeditor/`
- Override with `VOICE_WORKSHOP_HOME` or `--data-dir PATH` before the subcommand.
  Browser and agent operations must use the same directory.

Drafts live in local, unencrypted SQLite. The server is loopback-only, with no
analytics or model calls. Sharing a packet sends its text to your chosen agent
or chat and may consume usage. Imports do not overwrite source files. Review
findings yourself; prompts and validation cannot guarantee advice quality.

Back up to a new destination:

```bash
python3 "$HOME/.copilot/skills/copy-editor/scripts/workshop.py" backup "$HOME/Desktop/writing-backup.sqlite3"
```

## Reference

- [Workbench guide](references/workbench.md): commands, snapshots, progress, and comparisons.
- [External reviews](references/external-reviews.md): packets and result imports.
- [Pass catalog](references/pass-catalog.md): the 30 editing checks.
- [Agent instructions](SKILL.md) and [test report](TEST_REPORT.md).

Run core tests from this directory:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/anchors.test.cjs
```

Node and Playwright are development-only dependencies. Bundled Tailwind and
Public Sans assets retain their included licenses.

## Credits

An independent implementation of Thomas Ptacek's
[How To Write With An LLM](https://sockpuppet.org/blog/2026/09/17/how-to-write-with-an-llm/)
method, not his application's source. The first 16 check labels follow the supplied
screenshot; the other 14 checks and all detailed prompts were authored for this package.
