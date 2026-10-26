---
name: requirement-map
description: 'Map every added and removed line of a PR, branch, commit range or diff to a requirement, reconcile totals against git diff --numstat, and link each requirement to its wiki entry. Use when the user asks to map lines or code to requirements, count lines per requirement, audit scope creep, or trace a diff back to its spec or ticket.'
---

# Requirement map

Account for every added and removed line in a diff by assigning it to one requirement, split into production and test lines, with totals equal to `git diff --numstat` and each requirement linked to where it is recorded in the wiki.

## Steps

1. **Scope the diff and record the requirements.** Resolve `<base>` and `<head>` (for a stacked PR, `<base>` is the parent branch in the stack; `check_map.py` diffs `<base>...<head>`). Gather the requirements from the ticket, workstream page, spec, plan and review history.
   - When the repo has a `wiki/` directory, open the ticket or workstream page for the change, creating it per the wiki's schema if missing. Ensure its `## Requirements` section has one `### <ID>: <short summary>` heading per requirement, followed by one or two sentences stating what it requires and its source.
   - Reuse requirements already recorded on the page. Keep their IDs, headings and wording, and add only the missing ones. When the page records requirements in another form (bullets, acceptance criteria), add a heading for each under `## Requirements` and leave the original text in place.
   - Give review-driven or downstream-integration additions their own requirement headings (for example `### PANEL: Downstream debug-panel fields` or `### REC: Recording and pull lists`) so they stay distinct from core requirements and from `NONE`.
   - Reserve `NONE` for changes that trace to no requirement at all, such as unrelated fixes, stray formatting or unrequested refactors.
   - Keep `wiki/` links in local outputs only (chat, `scratch/`, `wiki/`). Never put `wiki/` paths in tracked files, commit messages or PR descriptions.

   Done when every requirement from the ticket, spec and review history has a `### <ID>: <short summary>` heading under `## Requirements` on the wiki page (when the repo has `wiki/`).

2. **Initialize the hunk map and classify every change.** Seed `scratch/<slug>-requirement-map.csv` (or `/tmp/requirement-map.csv`) from `git diff`:

   ```bash
   python3 <this skill's folder>/scripts/check_map.py scratch/<slug>-requirement-map.csv <base> <head> \
     --repo <checkout> --init-csv
   ```

   This writes `file,requirement,kind,added,removed,hunk` with exact per-hunk counts and marks each file `test` if it sits under `test/`, `tests/`, `__tests__/`, `spec/`, `specs/`, `testdata/` or `fixtures/`, or matches `test_*`, `*_test.*`, `*.test.*`, `*_spec.*` or `*.spec.*` (otherwise `prod`). Replace `TODO` on every row with one requirement ID (or `NONE`):
   - Single-requirement files can keep their hunk rows or collapse into one row per file with an empty `hunk`.
   - Multi-requirement production files assign each hunk row (or split a mixed hunk across rows that keep the same `hunk` range). Blank lines, comments, includes and function signatures go with the code they serve.
   - Multi-requirement test files split by test case according to what each case asserts. Shared helpers go with the requirement they serve. Setup shared inside a mixed test case splits in proportion to the case's assertion counts, rounded to integers by largest remainder (ties go to the requirement with the most assertions in that test).
   - Note any boundary rule where two requirements touch (such as a call site that counts a reason for one requirement while passing detail arguments for another) and how many lines move under the alternative reading.

   Done when no `TODO` rows remain in the CSV and you can cite every `NONE` change by `[file:line](path#Lline)` (using the surviving anchor line in `<head>` or the deleted file path for pure deletions).

3. **Verify reconciliation and wiki links.** Run (omit `--wiki-page` when the repo has no `wiki/`, or pass `--no-wiki` to skip wiki checks):

   ```bash
   python3 <this skill's folder>/scripts/check_map.py scratch/<slug>-requirement-map.csv <base> <head> \
     --repo <checkout> --wiki-page wiki/<page>.md
   ```

   Fix any file or hunk count mismatch and add any missing `### <ID>: <short summary>` heading under `## Requirements` on the wiki page. When recording the summary table on the wiki ticket page itself, re-run with `--link-style wiki` so requirement links use same-page `#<anchor>` targets instead of `wiki/<page>.md#L<line>`.

   Done when `check_map.py` exits 0 with 0 count mismatches and 0 missing requirement headings.

4. **Report the mapping.** Show:
   - The reconciled summary table and top file contributors from `check_map.py` (plus any unmapped wiki requirements with 0 lines in the diff).
   - Every `NONE` change with its link, what it changes, and whether to drop it or split it into its own PR.
   - The boundary rules used for ambiguous hunks and how many lines shift under the alternative reading.
