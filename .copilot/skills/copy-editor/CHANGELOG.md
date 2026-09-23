# Unreleased

- Keep the skill directly in dotfiles as `copy-editor`, without a separate repo
  or submodule fetch. Preserve the existing workbench data paths on rename.
- Explicitly support blank writing documents and verbatim PR-template imports,
  leaving all publishable prose and checkbox decisions to the author.
- Remove the duplicate Run elsewhere menu command; Review externally is the
  single export entry, while Import results stays directly available in the menu.
- Remove the built-in model runner, model-launch HTTP routes, and provider launch
  options. All evaluations now use external packets and imported results.
- Keep runtime installation to Python's standard library and bundled assets.
- Spell out the author-led revision loop and required fresh-evaluator A/B handoff,
  including isolation checks, result import, and delayed mapping disclosure.
- Add a visible Compare versions button that opens the A/B form directly. Label
  same-text snapshots and default comparisons to two distinct draft texts.

# 4.0.0 — External passes, shared results

- Add Run elsewhere and Import results controls, result-file upload and
  JSON paste, target preview, pending packet history and repeat downloads.
- Bind external replies to registered request IDs, exact snapshots, pass versions
  and input fingerprints. Reject guessed or mismatched destinations.
- Import into the existing reviews/issues store so all highlighting, status,
  history and checklist behavior is shared with native runs.
- Make identical imports idempotent, including concurrent imports; preserve the
  author's finding statuses. Reject conflicting second results for a packet.
- Add `external-packet`, offline `wrap-result`, and automatic-target `import-result`
  CLI commands. Local agents write directly to the shared store; the browser polls
  for their results. Remote chats return importable artifacts, not just prose.
- Keep feedback linked to its reviewed snapshot; do not count it toward checks
  for changed text. Export alone never completes a pass or calls a model.
- Back up v3 databases before an additive external-request migration. Retain legacy
  v2/v3 manual exchange and all 30 existing narrow checks.
- Add 25 deterministic exchange tests plus a dedicated Chromium interface suite.
  Existing browser tests now explicitly wait for asynchronous drawer opening.

# Changes

## 3.0.0 · September 19, 2026

- Add 30 independent, versioned check prompts and retain seven broad legacy modes.
- Add a grouped, searchable pass drawer with scope/filter controls, per-check
  counts, historical review access, running/error states, and exact-input progress.
- Preserve successful checks only for matching body, audience, purpose, and pass
  instructions; exclude demos and broad modes; reuse exact restored inputs.
- Add editable draft highlights with immediate stale-input removal, and safe
  Unicode-aware navigation to unchanged paragraphs without mutating prose.
- Add pass toolbar navigation, selectable pass-specific review history, explicit
  reviewed-text/editor controls, and idle refresh for agent-imported findings.
- Add `passes`, `progress`, per-snapshot progress API, and packet-version validation.
- Preserve v2 databases with a pre-migration SQLite backup and additive migration.
- Add 31 Python tests, 10 JavaScript tests, and a granular-pass browser suite.
- Retain no-rewrite/no-praise, author-controlled revisions, and fresh A/B workflow.

## 2.0.0

Add the runnable local writing workbench, snapshots, linked findings, Codex runner,
agent packet exchange, and fresh-process revision comparisons.

## 1.0.0

Initial diagnostic-only skill and behavioral acceptance scenarios.
