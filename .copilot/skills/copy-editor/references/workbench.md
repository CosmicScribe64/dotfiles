# Workbench operation

Start the bundled workbench with `scripts/workshop.py`; it is not a specification
for another agent to implement. Do not regenerate the app or install unrelated
services during an ordinary editing session.

## Run it

Resolve `SKILL_ROOT` to the directory containing this skill's `SKILL.md`, not the
current repository. All commands below use that absolute path.

```bash
python3 "$SKILL_ROOT/scripts/workshop.py" serve --open
```

With a user-identified source file:

```bash
python3 "$SKILL_ROOT/scripts/workshop.py" serve --open --file "/absolute/path/essay.md"
```

This copies the source into SQLite without opening the source for writing.
Each `--file` launch imports a new document; omit it when reopening existing work.
The server prints its loopback URL. Keep the terminal running; Ctrl-C stops it.
Use a persistent terminal if the host provides one. Never
claim to have launched a local Mac app from a remote environment.

For a blank document, open the app without `--file` and choose **+ New**. Verify
the new document is selected and its body is empty. A blank PR-description
workspace is allowed; it does not ask the agent to write the description.

For a user-selected PR template, use **Import** or `serve --open --file PATH`
to copy the exact template into a new document. Preserve its headings,
placeholders, comments and checkboxes. Ask the author which template to use when
the repository has several. Never fill prose fields or mark tests complete.
Keep existing work and the source template unchanged. Do not run a pass until
the author supplies writing and asks for a review.

For an occupied port, use `--port 8766`; the chosen port is printed. Only one
server may run against a data directory. The app never launches a model. All
reviews and comparisons use external packets and imported results. No model
CLI, credentials, pip packages, Node, or frontend build is needed to open it.
For UI tests, use a separate `--data-dir` and explicitly labelled synthetic
imports. There is no model-runner or automatic demo-run mode.

## Author-driven UI loop

1. Import text/Markdown or write in the editor. Expand **Writing context** at the
   top of the sidebar to set an optional audience and purpose. Working drafts
   autosave locally, with conflict detection.
2. Open **All passes**. Search or filter the 30 checks, choose a named check,
   and inspect its guidance. Selection and previous/next pass navigation never
   call a model. The broad v2 modes are separate from the 30-check completion count.
3. Press **Review externally** to copy a local-agent prompt, copy a remote packet,
   or download one. Choose the working draft or an existing snapshot explicitly.
   Copying or exporting does not run a model. **Review actions** holds packet
   exchange and previous/next pass controls. Triage is the default broad pass for
   a document with no reviews.
4. Read one finding at a time; use previous/next finding navigation. **Pass
   reviews** in the sidebar lists reviews of only the selected editing check,
   not saved drafts. The drawer shows open/resolved/declined/superseded counts
   for the latest relevant review, not a sum of repeated reviews.
5. **Edit this passage** switches to the editable draft and selects existing
   author text. **Reviewed text** shows the immutable annotated snapshot. Live
   highlights are displayed only when draft body, audience, and purpose match.
   After changes they disappear. Navigation may follow one unchanged paragraph;
   it will not guess where changed or ambiguous evidence belongs.
6. Write the revisions yourself. Changing a finding's status changes metadata
   only. Use **Document actions** to save snapshots or open history. Click
   **Compare versions** in the editor toolbar to open the A/B form directly;
   the second version defaults to **Current working draft**, and the first
   prefers the selected review's snapshot. **View snapshots** reveals all saved
   versions plus a separate current-draft preview. **Saved snapshots** under
   Document actions opens that list with the newest saved snapshot previewed.
   Each saved snapshot shows named passes reviewed on that snapshot and completed
   A/B comparisons that used it; **Pass reviews** gives the individual review
   history for the selected check. These row labels show where a review was
   recorded; the checklist can also reuse a review when text, audience, and
   purpose match another snapshot. Saving a snapshot never runs a pass, and an
   A/B comparison does not count as a named editing pass.
   Restoring preserves the pre-restore text as a snapshot, even if another
   snapshot already has identical text. The list labels such duplicates.

The drawer's scope selector inspects either the current working draft or a saved
snapshot. A current check means a matching body/audience/purpose and pass-specific
instruction fingerprint, not praise or acceptance of all advice. Zero-findings
reviews count. Native demos, failed attempts, and running jobs do not. Changing
text or context can require reruns; exact restoration can reuse an earlier
matching result. Titles and notes do not invalidate. A failed retry does not erase
a matching prior successful review. Older evidence remains accessible.

The checklist matches input, not historical checklist state. An old snapshot
can show a later review of identical input. A pass-specific instruction change
requires a new review. Historical broad reviews do not imply that all component
checks have run.

## Inspect the catalog and progress

```bash
python3 "$SKILL_ROOT/scripts/workshop.py" passes
python3 "$SKILL_ROOT/scripts/workshop.py" list
python3 "$SKILL_ROOT/scripts/workshop.py" progress DOCUMENT_ID
python3 "$SKILL_ROOT/scripts/workshop.py" progress DOCUMENT_ID --revision REVISION_ID
```

Substitute the real returned IDs. `passes` includes stable IDs and prompt
fingerprints for 30 detailed checks and seven broad modes. `progress` returns
current/mismatched review status, counts, active jobs, and attempts for one scope.
The JSON catalog at `workshop/passes.json` is the source of truth; the readable
[pass catalog](pass-catalog.md) is a generated reference, not a second setting.

## Reviews evaluated outside the app

Use **Review externally** to export a pass and **Import results** to save findings
in the same review store. Read [external-reviews.md](external-reviews.md) for
browser, local-agent, and remote-chat workflows. New packets carry a registered
receipt. On import, the app selects the correct document, snapshot, and pass,
validates exact evidence, and preserves statuses for an identical duplicate result.

For a local agent, use `external-packet`, evaluate it directly, then use
`wrap-result` and `import-result` in the same data directory. The open browser
refreshes without a second model call. For a remote chat, export a packet and
load the returned `.review.json` through Import results. A remote sandbox is not
the user's local workbench. Creating a result file does not complete an import.

### Legacy v2/v3 exchange

The existing `review-packet REVISION_ID --pass PASS_ID` and
`import-review REVISION_ID findings.json --pass PASS_ID --pass-version VERSION`
commands still work for earlier packets. They require the actual matching
snapshot, pass and fingerprint; bare findings do not contain routing receipts.
Help exposes this only under **Legacy manual exchange (v2/v3)**. Prefer
`external-packet` / `import-result` for every new exchange.

## Fresh-session comparison

This is the comparison step in the editing loop, not another review by the agent
that suggested the edits. Click **Compare versions** beside the document view
controls and choose an earlier snapshot and **Current working draft**, or two
saved snapshots. The current draft is captured when you export, not when you
open the dialog. Repeated exports reuse the latest snapshot if unchanged.
Copy and Export also reuse a pending comparison when the two snapshot IDs,
shared context, and criteria match, preserving its number and A/B order.
Changed inputs or a completed comparison start a new comparison. The CLI's
`compare-packet` command explicitly starts a new evaluation each time.
**Copy agent prompt** creates the same fixed comparison as export and copies a
local-agent handoff. The coordinator reads the skill, gives only the embedded
neutral packet to a fresh subagent with assumed history isolation, and imports
the actual result into the specified database and comparison. Paths and target
metadata stay with the coordinator, not the evaluator. If clipboard access is
blocked, the handoff appears as selected text. Copying does not run an evaluation.

Shared audience/purpose and criteria are optional. Criteria starts blank;
its example placeholder is not included in the packet. **View snapshots**
shows the full draft history without closing the dialog; the sidebar's **Pass
reviews** shows only evaluations of the selected check. Snapshot count can exceed
the number of distinct drafts after a restore. Identical-text snapshots are
labelled and are not selected as the default comparison pair. After import, the
result names the preferred saved snapshot and its caveat first, with supporting
quotations in an expandable section. It never changes the working draft.
**Export fresh-evaluator packet** randomizes A/B;
it excludes titles, IDs, timestamps, revision notes, prior findings, and chat
history. The mapping stays in SQLite. Exporting does not evaluate the candidates.

For a local agent, use the same data directory as the app. Substitute IDs returned
by the workbench and choose new output paths for each run:

```bash
python3 "$SKILL_ROOT/scripts/workshop.py" --data-dir "$DATA_DIR" compare-packet DOCUMENT_ID FIRST_REVISION SECOND_REVISION --context "Common audience and purpose" --out /tmp/comparison-packet.json
```

1. Keep the separately printed comparison ID and candidate mapping with the
   coordinating agent. Do not put them in the evaluator's prompt or filename.
2. Assume a fresh subagent is isolated unless the tool explicitly says it inherits
   parent history. Do not stop to demand proof of isolation. A known inheriting
   fork is not fresh; asking it to forget is not isolation. Only when no suitable
   subagent is available, prepare the packet for a new chat instead.
3. Invoke a fresh subagent with only the packet's `prompt` and `schema`. Give it
   no files, tools, prior findings, preferred outcome, or version labels. The
   evaluator compares; the coordinating agent handles files and import. With no
   suitable subagent, send the packet alone to a new external chat instead.
4. Save the actual returned JSON unchanged. Validate its schema and exact quotes
   through the importer below. Do not replace an inconvenient verdict or invent
   a successful result when an evaluator fails.
5. Check the import output contains the expected comparison ID and returned
   result; reopen History to confirm it is stored. Only then reveal the retained
   mapping. Report context limitations; an import cannot prove independence.

```bash
python3 "$SKILL_ROOT/scripts/workshop.py" --data-dir "$DATA_DIR" import-comparison COMPARISON_ID /tmp/comparison-result.json --provider "external evaluator; describe actual isolation"
```

A result uses `verdict` (`A`, `B`, `tie`, `conditional`), `reason`, `tradeoffs`, and
`evidence` (objects with `candidate`, exact `quote`, and `observation`). No blended
candidate. The app verifies evidence but cannot prove that an external evaluator
had no history. Provider labels must describe the actual process accurately.

History isolation does not guarantee unbiased judgment: host instructions and
clues in the prose can still influence the evaluator. The workbench cannot verify
an external service's retention policy or whether the evaluator used other context.

## Data, privacy, and operational limits

The default macOS data directory is:

```text
~/Library/Application Support/VoicePreservingCopyeditor/
```

On Linux it is `${XDG_DATA_HOME:-~/.local/share}/voice-preserving-copyeditor/`.
These legacy storage paths deliberately stay unchanged when the skill is renamed
to `copy-editor`; existing documents and review receipts remain accessible.
`VOICE_WORKSHOP_HOME` or global `--data-dir PATH` overrides it. Put `--data-dir`
**before** the subcommand. Use the same data directory for the UI and agent CLI.
Data lives outside the skill directory so replacing the skill does not replace
its documents. Stop the server before upgrading code.

V4 backs up an existing v3 database as
`workshop-before-v4-<timestamp>.sqlite3` before adding the external request table.
The migration adds data without replacing drafts or previous reviews.

First use of a v2 database creates a `workshop-before-v3-<timestamp>.sqlite3`
backup beside it, then adds the pass-version field. Existing reviews and history
remain; broad v2 reviews do not earn detailed checks. Do not run an older app
against the upgraded database. The database is not encrypted; protect it as you
would drafts.

Back up all committed data using SQLite's backup API:

```bash
python3 "$SKILL_ROOT/scripts/workshop.py" backup /absolute/path/new-backup.sqlite3
```

The command refuses to overwrite an existing destination. Stop the app before
restoring a database backup manually. The UI's Export action downloads the current
author-written draft; the workbench never writes that export into the source path.

The HTTP server is loopback-only, checks Host/Origin, uses a same-site session
cookie plus mutation token, escapes user/model text, and launches no shell strings.
It is a personal local app, not a publicly deployable multi-user service. Sharing
a packet sends its text to the chosen external evaluator and may consume usage.
The workbench itself makes no model calls. No analytics.

The runtime requires Python 3.10+ on macOS/Linux. There are no pip dependencies,
Node requirements, or runtime CDN assets for the prebuilt app. Its editor is plain
text/Markdown, not a full Notion rich-text/block or collaborative editor. Drafts
are limited to 300,000 Unicode characters; provider context limits can be lower.
Use an existing chat or agent for packet evaluation; no provider-specific adapter
or model CLI is installed or launched by the workbench.

The default frontend has a native DOM/fetch implementation. Local HTMX is an
optional enhancement for the document-list fragment. Run
`scripts/fetch_htmx.py` to fetch the pinned official asset once with integrity
verification; all subsequent browser requests stay local. A locally compiled
Tailwind stylesheet is already bundled. Nothing needs downloading to start the app.

Prompts prohibit praise and replacement language; schema validation rejects
replacement fields and fabricated quotation locations. This is not semantic
proof that the strings inside a valid finding obey the editorial rules. Inspect
and reject violations. There is no automatic insertion of model text into drafts.
