# Git scope

Use for diff requests, pre-commit staged reviews, and repository requests with no
explicit target. A supplied paragraph or current-file selection does not need Git
bookkeeping. The main skill governs mode and edit permission.

## Resolve the fixture

1. Record the repository root, current `HEAD`, requested refs, and resolved commit
   hashes. Pin commits once; branch movement must not change the source mid-review.
2. Use explicit refs exactly: two refs or `base..head` compare snapshots directly;
   `base...head` or an explicit merge-base request compares the merge base to the head.
   A requested current-file, staged-only, or unstaged-only view keeps that scope.
3. With no target, compare `HEAD` against its merge base with the established default
   branch, preferring the locally recorded remote-default ref for the intended remote.
   Do not assume `origin`, `main`, or `master`. On the default branch itself, use the
   remote-default ref, not the local branch, so unpushed commits stay visible; a local
   default branch can still be the base for a different branch. Ask if the base is
   missing or ambiguous; do not guess or fetch.
4. Only when that default branch diff is empty, inspect staged, unstaged, and untracked
   non-ignored changes. Inspect index and worktree differences separately even if they
   cancel in the net diff. An explicit scope never falls back to another version.
5. Stop with `scope mismatch` on an unresolved ref/path or a source that disagrees with
   the pinned fixture. Report what was observed; do not substitute remembered text,
   another branch, or the worktree. If no relevant changes exist, report that and stop.

Keep the full fixture record internal unless requested or needed to explain a mismatch.
State enough scope in the result to identify the audited versions; do not print a
large manifest for a small edit.

## Inventory the changes

Use the changed-file list and diffstat, then inspect added, changed, and removed writing
blocks. Include documentation, headers, shell, configuration, and Starlark/Bazel rather
than relying on a source-extension grep. Parse comments by language when possible;
otherwise inspect the actual syntax and state any inventory limit.

Treat contiguous comments/docstrings as blocks. Read deleted files at the base and
check removals for lost requirements, rationale, or dangling references. A deliberate
deletion is not permission to restore the text. Compare at least one extracted block
with its exact source version when the inventory is nonempty. Read nearby unchanged
material only for meaning, duplication, and continuity. An empty writing inventory
does not authorize executable cleanup.

## Separate inspection from mutation

Historical audits read the requested revision without checkout; no clean worktree or
editable mapping is needed. Diff line references identify the appropriate base/head
version, not an unrelated current file.

Before an in-place rewrite, confirm that the target block still matches the inspected
version and preserve unrelated staged/unstaged changes. If it changed, reread only
when the current working version is authorized; otherwise report `scope mismatch` for
that target and leave it alone. Refs do not authorize reset, checkout, stash, or an
overwrite to make the working tree match.

A staged-only rewrite does not implicitly authorize index changes. Propose a patch
unless the user also authorizes its editable destination. The exception is a
pre-commit review inside an authorized commit task: apply its fixes to the working
files and restage only those intended changes. Check the destination immediately
before applying a fix. Inspect the final diff for unrelated churn; cleanup alone does
not authorize staging, committing, or pushing.
