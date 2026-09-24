---
description: "Personal defaults for focused changes, mandatory pre-commit deslop, Git scope, operational evidence, and C++ work."
applyTo: "**"
---

# Agent Instructions

## Core Defaults
- Make the smallest clear, maintainable change that fully addresses the request. Prefer a direct local solution; add abstractions, optimizations, refactors, or scope only when current complexity or demonstrated duplication justifies them, not for hypothetical future requirements.
- Write plainly and concisely in accordance with the plain-language principles in ISO 24495-1. State assumptions, evidence, tradeoffs, and unresolved risks directly; omit filler and repeated summaries.
- Preserve unrelated user changes. If they affect the task, work with them; if they make the task unsafe or impossible, stop and ask.
- Read the controlling code and nearby tests before editing. Validate the changed behavior with the narrowest useful check, and report checks you could not run.

## Pushback and Alternatives
- Raise any materially better approach, flawed assumption, missed case, safety concern, or excessive scope as soon as identified. Explain the practical tradeoff once, then follow the user’s decision.
- Do not manufacture objections when the requested approach is reasonable.
- If the user chooses an approach you advised against, implement it without repeatedly relitigating the decision and record any material residual risk in the final response.

## Scope
- Do not modify files when the user asks only for an explanation, diagram, review, or command output.
- Treat explicit exclusions and words such as "just" and "only" as hard scope boundaries.
- Ask before expanding scope or taking an external action the user has not requested. Approval of wording does not authorize posting, committing, or pushing it.

## Before Every Commit
- Before every commit, including amendments and review-fix commits, follow the `deslop` skill's pre-commit review on the exact staged content. It covers comments and docstrings in source and build files, and it checks whether each new document is needed before its wording is polished. Loading the skill earlier or reviewing only the PR description does not count.
- Within the authorized scope, remove unnecessary agent-authored documents. Ask before edits or deletions outside that scope.
- Restage only the intended changes. Recheck the staged writing after any later edit or staging change.
- Before committing, briefly report the reviewed scope and the fixes or remaining findings, or confirm there is no prose change. Formatter, lint, link, and test results do not replace this review. Stop before committing if the review cannot run or a material finding needs resolution or approval.
- The review covers writing only. It does not authorize code cleanup, commits, or pushes, and it does not need a report file.

## Git Completion
Before claiming that commit, push, or pull-request work is complete:
1. Recheck the current branch and worktree with `git status --short --branch`.
2. Inspect the branch diff against the intended base branch.
3. For a commit, verify that it contains every intended change and excludes unrelated working documents, local configuration, generated output, and pre-existing changes unless the user explicitly included them.
4. For a requested push or PR, verify that the intended commits are pushed and recheck local and remote branch parity. A commit-only request does not authorize a push or PR.

## Operational State and Evidence
- Treat the worktree, branch, `HEAD`, network, credentials, Kubernetes context, running processes, and deployed artifacts and configuration as volatile. Recheck relevant state after any event that could invalidate an earlier observation.
- In runtime, hardware, and deployment diagnosis, label observations separately from hypotheses.
- Before claiming a runtime fix or success, verify the running artifact and configuration and collect end-to-end evidence at the failing boundary. A successful build, render, push, or deploy alone is not runtime proof.

## Manual Command Output
When the user must run a diagnostic command:
- Provide one paste-and-run block, not a script file or a sequence of separate commands.
- Send stdout and stderr to a report under `/tmp`. Read the report yourself when tools can access it; never ask the user to paste its contents.
- Keep probes bounded and non-interactive. Use `timeout` for network probes, and `ssh -n` or `</dev/null` so repeated SSH commands do not consume stdin. `ssh -n` cannot be combined with a heredoc-fed remote script.
- Put `REPORT` and tunable variables at the top, and validate required variables and files immediately before use.
- Use `set -uo pipefail` for best-effort diagnostics and `set -euo pipefail` for fail-fast build, push, or deploy blocks.
- Print relevant resolved identifiers in the report, and end with greppable `key=true` or `key=false` verdicts when practical.

Adapt this template. It starts with `date -Is`, guards expected probe failures with `|| true`, and prints the exact report path outside the redirected group:

```bash
export REPORT=/tmp/<topic>-check.txt
export <ANY_OTHER_VARS_THE_BLOCK_NEEDS>=...
( set -uo pipefail
  test -n "$REPORT"
  {
    echo '=== TIMESTAMP ==='
    date -Is
    echo
    echo '=== <SECTION NAME> ==='
    <command> || true
    echo
    echo '=== QUICK VERDICT HEURISTICS ==='
    if <condition>; then echo '<key>=true'; else echo '<key>=false'; fi
  } >"$REPORT" 2>&1
)
printf '<Topic> report: %s\n' "$REPORT"
```

## Generated Working Documents
- Store AI-generated plans, specs, TODOs, research, and similar working documents in the repository's top-level `scratch/` directory.
- Before creating one, verify that the top-level `scratch/` directory is ignored. If it is not, add `/scratch/` to the repository-local `.git/info/exclude`; do not modify a tracked `.gitignore` solely for generated working documents.

## Repository Conventions
- Follow the repository's release and dependency policies. Avoid unrelated version bumps and lockfile changes.
- Run the repository's formatter on changed files before completion and before any commit. Do not format unrelated files.

### C++ Style
- Use descriptive identifiers except for obvious, local indices or coordinates.
- Prefix enum values and namespace-scope constants with `k`, for example `kFollowing` and `kMaxTrackIndex`.
- Replace protocol, hardware, and sensor magic numbers with named domain-header constants and a short bound or wire-meaning comment.
- Prefer existing conversion functions and utilities over duplicate arithmetic.
- Prefer `std::string_view` for non-owning constant strings and return values.
- In compound conditions involving `std::optional`, use explicit `has_value()` and `value()`.
- Document every function declaration in headers, including private helpers. Group override declarations under one comment only when that comment accurately defines each contract.
- Mark computed values `const` unless later mutated.

## PR Descriptions
- Use `gh api` whenever updating a pull-request description; other methods have caused errors.
- Use this structure when drafting or updating a PR description. Fill it with verified facts; leave test boxes unchecked unless those steps were actually completed. Include screenshots or recordings only when useful and safe to share.
- For stacked PRs, append the required Stack navigation section after this structure.

```markdown
## Why
<!-- The motivation or ticket/issue this addresses (e.g., closes #123). -->

## What
<!-- A clear, short summary of what this PR does. -->

## How
<!-- Brief notes on the technical implementation or key changes. -->

## How to Test
<!-- Step-by-step instructions for the reviewer to verify the changes. -->
- [ ] Step 1:
- [ ] Step 2:
```

## Stacked PR Workflow
- For all stack work, check supported commands and APIs against GitHub's current [overview](https://docs.github.com/en/pull-requests/get-started/about-stacked-prs) and [workflow docs](https://docs.github.com/en/pull-requests/how-tos/stacked-pull-requests).

### Create and Review
- Keep PRs focused, buildable, and small enough to review against their immediate base. Dependencies belong in the same or a lower layer.
- Use branches in one repository: bottom PR targets the intended trunk; each later PR targets its predecessor. Preserve PR identities and requested draft states.
- Register existing PRs with `gh stack` or the REST stack API. Branch chains and description links are not native stacks; report a blocker if registration is unavailable.

### Update and Merge
- Recheck remote membership, branch heads, bases, and worktree before changes; preserve unrelated work.
- Fix the owning layer, restack affected descendants with the supported workflow, and rerun relevant checks. Use lease-protected pushes for rewritten branches, never unconditional force pushes.
- Merge only when requested, with approvals and required CI checked for every included layer. Confirm scope: merging an upper PR can also merge those below it.
- After registration, pushes, restacks, or merges, verify native membership/order, bases, incremental diffs, and local/remote parity. Verify automatic rebases and retargeting before further changes.

### Navigation Format
- Replace each PR's stack section with `## Stack navigation`, then `Merge in this order; each PR targets its predecessor:` and a numbered list of the full stack in merge order, including itself.
- Each entry: `[<full PR title> #<number>](<PR URL>)`, an em dash, and a short scope label. Retain bracketed title prefixes such as `[Validator authoring 1/4]`.
- Keep titles, numbering, and the identical navigation list current across all PRs. Preserve description content outside this section.
