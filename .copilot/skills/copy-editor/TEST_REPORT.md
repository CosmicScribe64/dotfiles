# Current validation · first-party copy-editor

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
