# Git scope

Use for diff requests, staged reviews, and repository requests without a target. A
pasted paragraph or a selection needs none of this.

## Resolve what to review

1. Use explicit refs exactly and pin their commits once. `base..head` or two refs
   compare snapshots; `base...head` compares the merge base to the head. A requested
   file, staged-only, or unstaged-only view keeps that scope.
2. With no target, compare `HEAD` with its merge base on the default branch, using the
   recorded remote-default ref (not an assumed `origin/main`). On the default branch
   itself, use the remote ref so unpushed commits stay visible. Ask if the base is
   missing or ambiguous; do not fetch.
3. Only when that diff is empty, inspect staged, unstaged, and untracked non-ignored
   changes, checking index and worktree separately.
4. Report `scope mismatch` for an unresolved ref or path. If nothing relevant changed,
   say so and stop; do not widen to a whole-tree cleanup.

## Inventory

Inspect added, changed, and removed writing in every file type, including headers,
shell, configuration, and build files. Treat contiguous comments as blocks. For deleted
text, check for lost requirements or dangling references; a deliberate deletion is not
permission to restore it.

## Inspect versus edit

Historical audits read the revision without checkout. Before editing in place, confirm
the target still matches what you inspected and preserve unrelated staged and unstaged
changes. Never reset, checkout, or stash to make the worktree match.

A staged-only rewrite does not authorize index changes; propose a patch unless the user
also authorizes the destination. The exception is a pre-commit review inside an
authorized commit, which edits the working files and restages only its fixes. Cleanup
alone never authorizes staging, committing, or pushing.
