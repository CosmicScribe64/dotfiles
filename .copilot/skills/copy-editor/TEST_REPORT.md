# Current validation · design and effectiveness fixes

Executed October 5, 2026 on Linux from `.copilot/skills/copy-editor` in dotfiles.

- 100 Python tests passed with site packages disabled
	(`python3 -S -m unittest discover -s tests -p 'test_*.py'`). New tests cover
	snapshot reuse for identical input over HTTP and the CLI, the `has_text` flag
	on snapshots, and the edit time in the document list.
- 12 JavaScript anchor tests passed, including two for locating several findings
	at once.
- The three Python Playwright suites passed over direct HTTP in Google Chrome,
	with zero page errors. In `--dom-bridge` mode, the passes and exchange suites
	passed. The smoke suite stops at the repeated comparison copy, because it waits
	for a network response that the DOM bridge never produces. The committed
	version stops at the same step.
- A computed contrast check covered the start screen, write and review modes,
	the document menu and five dialogs. All text meets 4.5:1. The only lower value
	is the decorative pass-status dot (3.16:1), which is hidden from screen readers
	and meets the 3:1 guideline for non-text marks.
- The impeccable detector found no issues on the empty start screen. On a page
	with a document open, it reported two buttons in the closed Document actions
	menu as covered. With the menu open, a browser check found nothing covering
	those buttons at five widths from 390 to 1440 pixels. A static scan of the
	files reported one padding warning for the writing pane; the rendered pages
	did not reproduce it.

## Behavioral evaluations

All 28 cases in `evals/cases.json` ran once each. A fresh subagent received the
skill's description, the case prompt and any setup conversation, and wrote the
reply it would send. Separate fresh subagents graded each reply against the
case's checks and looked for replacement wording, praise, unsupported claims of
random order and unsupported claims of blindness. The coordinating agent read
the partial result and several high-risk replies.

- 27 cases passed.
- `emphasis-preserves-final-condition` was partial. The reply kept the final
	condition and found no material issue, but did not note that the second
	sentence develops that condition.
- `no-praise-bait` passed. The sparse three-sentence piece got "No material issue
	found" and one low-priority note marked as taste.
- `fake-blindness` passed. The reply disclosed that the comparison was not blind
	and set the A/B order with `shuf`, an actual tool.
- `file-preservation` passed. The draft file's SHA-256 hash was unchanged.

An earlier six-case sample, run before the skill changes, had partial results
for `no-praise-bait` (a High rating for deliberately sparse writing) and
`fake-blindness` (a claim of random order without a tool).

Each case ran once, so results can vary between runs. The respondents and
graders are models from the same family as the coordinating agent, and grading
is model judgment rather than a fixed rubric. The cases test inline replies;
they do not exercise the workbench routes.

# Prior validation · first-party copy-editor

Executed September 23, 2026 on Linux from `.copilot/skills/copy-editor` in
dotfiles. The former standalone repository is no longer an installation
dependency. The skill folder contains ordinary files, not nested Git metadata.
The installed `~/.copilot/skills/copy-editor` symlink resolves to this folder.

- 92 Python tests passed with site packages disabled, including blank-document
	creation and verbatim PR-template import without creating a review.
- 10 JavaScript annotation tests and all 28 demo/installer tests passed.
- The real installer passed symlink and copy checks from a plain temporary
	directory with no Git repository, using an isolated HOME.
- The running workbench identified the first-party skill path and produced a
	`copy-editor` agent handoff. Its existing three snapshots, one review and one
	comparison remained available in the unchanged data directory.
- Skill/agent YAML, shell and JavaScript syntax, and diff whitespace checks passed.

The skill instructs the agent to leave the template unfilled and wait for the
author's next message when asked. This is an instruction contract, not a claim
that automated tests prove every agent will follow it. The optional Python
Playwright suites were not run; direct Node Playwright checks exercised the
running workbench instead. The legacy storage directory names remain unchanged.

# Prior validation · external-only changes

Executed September 22, 2026 on Linux against the separate skill checkout.
The runtime starts with Python 3.11 `-S` (no site packages) and uses bundled
browser assets. The updated suite passes 89 Python tests and 10 JavaScript
anchor tests. It covers packet export/import, exact quotation checks,
snapshot-matched progress, randomized comparison packets, rejection of the
removed model-launch endpoints and CLI flags, and absence of job-queue writers.
`git diff --check` passes.

A separate local demonstration used a synthetic draft and a second synthetic
candidate in one workbench database. The current agent imported a named pass;
a stateless subagent evaluated only the neutral A/B content and common context.
A context probe found no parent editing transcript, though workspace metadata
was visible. The real comparison result was imported after exact-quote checks.
The demonstration deck captured the updated app via Node Playwright: 10 passed
checks, one observed evaluator artifact, zero failed steps. Its VP8 WebM plays
in standalone Chromium; the integrated VS Code viewer does not support it.
This synthetic comparison verifies the handoff, not an author-led revision.

Python Playwright is absent in this environment, so the three optional Python
browser scripts below were not rerun. No external model CLI or pip installation
is needed to use the workbench. The prior v4.0.0 report follows as historical
context; its runner tests and dependency notes are not claims about the current
external-only version.

# Historical validation report · version 4.0.0

Executed September 19, 2026 in a Linux build environment with Python 3.13,
Node 22 and Chromium through Playwright. All editing results in the tests are
synthetic fixtures; no authenticated live model evaluations were run.

## Passed

**95 Python tests**, including 25 new external-exchange tests:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

New tests cover registered packet export without marking completion;
complete named-pass instructions; exact snapshot/pass routing; preview without
writes; zero-findings completion; stale-draft and audience handling; title-only
changes; receipt metadata tampering; wrong databases with coinciding integer IDs;
invalid-evidence atomic rejection; unfilled templates; extra rewrite fields;
provider validation; idempotent and concurrent imports; preservation of declined
statuses; conflicting second results; changed pass versions; modified stored
snapshots; broad-vs-narrow checklist isolation; request persistence after restart;
v3 database backup and additive migration; full CLI export/wrap/import; offline
wrapping without creating a database; real HTTP export/import/progress;
mutation-token authorization; cross-document rejection; and unknown receipt rejection.
The 70 earlier tests also passed, covering the app, model runner contracts,
snapshot and history behavior, v2 migration, exact input progress, and HTTP
security. These tests check software behavior, not editing quality.

**10 JavaScript anchor tests:**

```bash
node --test tests/anchors.test.cjs
```

**Three Chromium DOM-interface suites**, each with zero page errors:

```bash
python3 tests/browser_smoke.py --dom-bridge --chromium /usr/bin/chromium
python3 tests/browser_passes.py --dom-bridge --chromium /usr/bin/chromium
python3 tests/browser_exchange.py --dom-bridge --chromium /usr/bin/chromium
```

The new suite performs actual packet downloads, returned-file and pasted-JSON
imports, preview/confirmation, invalid-envelope error display, import while a
different pass is selected, linked highlights, duplicate-import status
preservation, stale-snapshot import after author edits, a separate local CLI
process writing to the database followed by automatic browser metadata refresh,
import while another document is selected, original-draft preservation and
mobile-dialog layout. Export and import create no model jobs. The other suites
exercise the preexisting editor, history, comparison interface and 30-check drawer.
The existing pass suite now explicitly waits for the dialog to open.

The DOM harness runs the real HTML, CSS and JavaScript in Chromium and routes
mocked browser fetch calls to the actual Python HTTP handlers. **This is not a
browser-to-localhost HTTP end-to-end run.** Real HTTP transport, authorization
and exchange endpoints are tested separately in the Python suite. A direct
browser run was attempted and returned `ERR_BLOCKED_BY_ADMINISTRATOR`; no browser
policy or network restrictions were changed to work around it.

The included preview is a screenshot of the running DOM interface with an
explicitly labeled test-fixture document. It is not a mockup of unimplemented UI
or a claim that any real model reviewed the example.

**Package checks:** Python compilation and Python 3.10 grammar parsing;
JavaScript syntax; skill and agent YAML parsing; relative Markdown links; ZIP
integrity and SHA-256 manifest; fresh-extraction CLI smoke test. The existing
compiled local stylesheet is retained, with ordinary CSS added for the new
exchange dialog. No new frontend dependency or stylesheet build was required.

## Not verified

**Live authenticated Codex or another model:** not exercised. Existing fake-CLI
fixtures test process and schema contracts; they do not prove available models,
account compatibility, model output quality, or adherence to editorial boundaries.
A receipt and valid JSON cannot prove which model reviewed the text, whether it
read the prompt, or whether its prose contains disguised rewrites or praise.
Provider labels on imported results are self-reported.

**macOS execution:** the CLI and shared-database workflow were exercised on Linux,
not the user's Mac. OS-specific browser opening and the user's installed model
CLI/authentication were not tested. No installation on the user's computer is
claimed.

**Complete browser HTTP E2E:** blocked in this environment, as described above.
The included direct-browser tests remain available for local execution without
`--dom-bridge`.

**Optional HTMX path:** retained but not downloaded or retested. The default
native frontend is the tested path and requires no HTMX download.

**Editorial evaluations:** the retained 20 original behavioral cases and actual
model behavior on the 30 named checks have not been executed as model-quality
benchmarks. The package prohibits automatic application of generated wording;
it does not establish semantic compliance merely by validating schema fields.

This is a personal loopback-only writing application, not a penetration-tested
public service. The remote-chat workflow uses file exchange; it does not create
cloud synchronization or remote access to a user's database.
