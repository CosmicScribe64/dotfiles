# External passes and a shared workbench

The application, local agent and remote chat use the same named pass definitions
and finding schema. Only the evaluation location differs. Returned findings go
into the existing reviews/issues tables and participate in the same annotations,
status controls, history and exact-input checklist. No model call is triggered by
export, wrapping, validation or import.

## In the browser

Select a pass and click **Review externally**. Choose the working draft or an existing
snapshot. The working-draft route first saves an exact snapshot.

- **Copy agent prompt:** for an agent on this computer. The prompt identifies the
  installed skill, actual data directory, document, snapshot, and pass version.
  It includes a CLI argument array to retrieve the pass. It contains no draft text
  or session token. The agent evaluates the packet and imports directly; no manual
  file transfer is needed. Stop if the packet's target or pass version differs.
- **Copy packet JSON:** for a remote chat. Paste the complete packet into the chat;
  it includes the named pass, full draft and context, relevant declined findings,
  return schema, and reply template. Share only with the intended evaluator.
- **Download pass packet:** the same self-contained packet as a `.packet.json`
  attachment, with a separate chat instruction shown in the dialog.

Copying does not run a model or complete a check. If clipboard access is denied,
the handoff remains selected in a read-only field for manual copying. Choosing
another snapshot clears that displayed handoff; already copied text still targets
its original snapshot, not the latest draft.

Ask the evaluator to return the completed `.review.json`. **Import results**
accepts that file or pasted JSON, including a single enclosing JSON code fence.
It validates and previews the target document, pass, snapshot, finding count,
reviewer label and whether the saved working input still matches. Confirm the
import to store it. The app selects the correct document/pass automatically;
current selection is not used to route the result. Zero-findings results count.

Packets are recorded locally as awaiting a result and can be downloaded again
from the dialog. Exporting a packet does not complete any checklist item.
The v2/v3 exchange remains in the **Legacy manual exchange** section for old
packets only. It cannot infer missing receipt metadata.

## From a local agent (no manual transfer)

Use IDs returned by the app. Do not substitute another data directory because it
has documents with similar names. Resolve `SKILL_ROOT` to the installed skill
directory. A copied local-agent prompt supplies these paths and IDs as
`TARGET_JSON`; use its exact snapshot and verify the exported pass version.

```bash
python3 "$SKILL_ROOT/scripts/workshop.py" list
python3 "$SKILL_ROOT/scripts/workshop.py" external-packet DOCUMENT_ID \
  --pass find-real-actors --out /tmp/actors.packet.json
```

Select a requested existing snapshot with `--revision REVISION_ID`. Otherwise
the command snapshots the current saved working draft. Read the complete packet,
perform only its check, and write a separate findings file containing
`scope` and `issues` with the supplied issue schema. Do not edit the source draft.
Then preserve the receipt automatically:

```bash
python3 "$SKILL_ROOT/scripts/workshop.py" wrap-result \
  /tmp/actors.packet.json /tmp/actors-findings.json \
  --provider "current local agent" --out /tmp/actors.review.json
python3 "$SKILL_ROOT/scripts/workshop.py" import-result /tmp/actors.review.json --check
python3 "$SKILL_ROOT/scripts/workshop.py" import-result /tmp/actors.review.json
python3 "$SKILL_ROOT/scripts/workshop.py" progress DOCUMENT_ID
```

The `--check` operation is an optional read-only preflight. Import needs no manual
revision or pass arguments: they come from the registered receipt. Use a truthful
provider label. Exchange output commands refuse to overwrite an existing file;
choose new paths for subsequent runs. Add global `--data-dir /actual/app/data`
**before** the subcommand when the app uses a nondefault directory.

The browser polls metadata roughly every five seconds while idle and displays
new reviews for the selected pass. Other passes update in the checklist and
history. This refresh never replaces the text in the editor. The app can be
closed during a local CLI import; the review is present when reopened.

## From a chat without access to the user's computer

An exported packet is sufficient. Its top-level `instructions` field explains
the exchange; `prompt` includes the exact pass and draft data. Follow
`result_schema` and `reply_template` for the reply. Preserve the `format` value
and complete `request` object verbatim; replace the provider/scope placeholders,
and fill the result. Do not create a second workbench or send the draft to
another model. Use file tools only to read the supplied packet and create its
JSON result, not to inspect unrelated files or session history.

`wrap-result` can also wrap inner findings offline. It only reads its input files
and writes the result. It does **not** open or create a database,
start a server or call a model. A chat with the bundled script can use that helper
without access to the Mac. Without a script, construct the same envelope from the
reply template and validate its exact fields and evidence before returning it.

Return a `.review.json` attachment. If file creation is unavailable,
return one JSON code block the author can paste into Import results. A prose
review alone cannot update the app. There is no cloud sync or automatic access
from a remote chat to the user's local SQLite database.

## Validation and limits

Each result carries an opaque request ID plus document/revision IDs, a pass
instruction fingerprint and a SHA-256 fingerprint of body/audience/purpose. The
ID must have been exported from the receiving database, and its metadata must
match the stored packet. This prevents ordinary wrong-database, wrong-snapshot
and wrong-pass imports; it is not authentication of a model or its behavior.

The importer checks the result schema and every exact quotation before committing
all findings and the receipt in one SQLite transaction. If text changed after
export, the result still belongs to the old snapshot. Its check is current only
for matching input. Changed pass instructions require a new review packet.

Reimporting an identical result returns the existing review without duplicating
findings or resetting resolved/declined statuses. A different second result is
rejected: export another packet for another run. Multiple agents/tabs importing
the same reply concurrently cannot create duplicate reviews.

Unfilled templates, invalid quotations, guessed receipts and extra replacement
fields are rejected. No import overwrites author text. The reviewer label is
self-reported; schema validation is not a semantic guarantee of editorial quality,
no praise, no replacement wording, or evaluator independence. Inspect findings.
A remote chat may have different context limits; the packet can be large. Result
upload/paste is limited to 1.9 MB in the UI and exchange file reads to 2 MB in the
CLI. Read the complete draft rather than silently reviewing a truncated packet.

The packet contains the actual writing and context. Share it only with the
intended evaluator. Retain or delete downloaded copies as appropriate. Export is
local; attaching the packet to a chat shares its contents with that service.
