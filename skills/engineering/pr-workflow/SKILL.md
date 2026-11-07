---
name: pr-workflow
description: "Commit, write or update a PR description, and manage stacked PRs. Use when committing, opening or editing a PR, or building, restacking, or merging a PR stack."
---

# PR workflow

A request to commit never authorizes a push or PR, and approving wording never authorizes posting it.

## Commit

1. Check `git status --short --branch` and the diff against the target base branch.
2. Confirm the commit holds every intended change and none of: working docs, local config, generated output, or edits that were there before you started.

## PR description

Update the body with `gh api`, in these sections:

- `## Why`
- `## What`: open with a small Mermaid graph of the change (data flow, call flow, or components), shading new or changed parts. Render it once (for example `minlag/mermaid-cli` in Docker) before posting.
- `## How`
- `## How to Test`: leave checkboxes unchecked unless the test actually ran.

After a push, check the local and remote branches point at the same commit.

## Stacked PRs

Check GitHub's [stacked PR overview](https://docs.github.com/en/pull-requests/get-started/about-stacked-prs) and [workflow docs](https://docs.github.com/en/pull-requests/how-tos/stacked-pull-requests) first.

- Keep each layer small and buildable in one repo. The bottom PR targets trunk and each later PR targets its predecessor; dependencies stay in the same or a lower layer. Register the stack with `gh stack` or the REST stack API, and report a blocker if neither is available.
- Fix a problem in the layer that owns it, restack the layers above, and push rewritten branches with `--force-with-lease`.
- Merge only when asked, after checking approvals, CI, and what the upper PRs would merge. After any change, recheck stack order, bases, diffs, and remote parity.
- End every PR in the stack with the same section:

  ```markdown
  ## Stack navigation

  Merge in this order; each PR targets its predecessor:

  1. [<full PR title> #<number>](<PR URL>) — <short scope label>
  ```
