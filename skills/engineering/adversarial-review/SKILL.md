---
name: adversarial-review
description: "Adversarial correctness review of a code change by fresh subagents that try to break it: they trace every changed value through its unchanged producers and consumers, sweep a defect-class checklist, prove findings by running code, and repeat on every push until a pass is clean. Use when reviewing a PR, branch or diff for bugs, re-reviewing after fix commits, or asked for an adversarial review."
---

# Adversarial review

Finds bugs in a change: wrong behaviour, lost data, false status, and tests that cannot fail. Style is out of scope except breaches of rules the repo writes down, reported as Nits. The reviewer is always a fresh subagent that did not write or discuss the change, briefed to break it rather than confirm it. Three habits:

- **Trace**: every value the diff touches is followed into the unchanged code that produces and consumes it. Most missed bugs sit one hop outside the diff.
- **Sweep**: a fixed checklist of defect classes, and every sibling of each instance found.
- **Loop**: a fresh reviewer on every push, fix commits included, until a pass is clean.

## When to run

- Before asking for human review of a PR, and again on every push, including pushes that only answer review comments.
- This skill does not replace other reviewers. If an independent automated PR reviewer is available (for example GitHub Copilot review), keep it running on every push too. On seven held-out PRs this skill caught about 80% of Copilot's correctness findings and found 11 further valid bugs Copilot did not; the two overlap only partly.

## Process

### 1. Pin the pass

1. Review a pushed or committed SHA, never a working tree that will be rewritten. Record `HEAD` as the pass SHA.
2. Base: the PR's merge-base with its target, or the ref the user gives. Check `git rev-parse` and a non-empty diff before dispatching anything.
3. Find the last reviewed SHA: the newest `adversarial-review-<branch>-<sha>*.md` report in the repo's untracked notes directory (`scratch/` or its local equivalent; slashes in the branch become `-`).
4. Pick the range:
   - **Full pass** `<base>...HEAD`: no earlier report, or the last reviewed SHA is no longer an ancestor of `HEAD` after a rebase.
   - **Incremental pass** `<last-reviewed>..HEAD`, plus the whole function or component around every hunk. Fixes break their neighbours: a new tie-break, a sibling field left unreset, a README the fix made stale.

### 2. Split by area

Over about 15 files or 1,000 changed lines, split the range by area (module, layer or language) into parallel reviewers. The split assigns hunks only; every reviewer gets the full changed-file list and traces across areas.

### 3. Brief

Fill [reviewer-brief.md](reviewer-brief.md) and paste it with [defect-classes.md](defect-classes.md) in full; the reviewer has no other access to them. The brief carries exactly four inputs:

- the range, SHA, worktree path and the area's hunks
- the spec or ticket text, as requirements; the reviewer also reads standing requirement and architecture documents in the touched directories
- the PR body, under "Author's claims", as statements to verify
- earlier Confirmed findings and their fix commits, under "Verify fixed"

Everything else the author believes stays out: summaries of what the PR does, focus lists, "already checked", "known gaps", "accepted", "do not re-report". Such lists steer the reviewer away from the code most likely to hold the next bug.

### 4. Dispatch

- Use a general-purpose agent with a terminal and file access, on the strongest model tier available. A read-only search agent cannot run tests or mutations.
- Start one fresh reviewer per area per pass. Nothing from earlier passes carries over except "Verify fixed".
- Give each reviewer its own worktree at the pass SHA (`git worktree add --detach <tmp-dir> <sha>`) and remove it afterwards. Parallel mutations in one tree clobber each other and the author's uncommitted work.
- Parallel agents can share one terminal and read each other's output. Tell each reviewer to read files with its file-reading tool and to redirect every command's output to its own work directory, then read it from there.
- Set no time, word or finding budget. Allow tests, scripts, real data and a browser for UI. Dispatch all areas together in the foreground and wait for every report.

### 5. Triage

1. Redispatch any area whose report lacks a Traced line for a changed value or a verdict for a checklist class.
2. **Suspected** items: reproduce each one (failing test, script, data query) or trace its trigger input to the code that produces it, then mark it Confirmed or dropped with that evidence. A dismissal as "misconfiguration", "user error" or "unlikely" cites the producer file:line showing the input cannot arise; when the change's own code writes that input, the item is Confirmed.
3. Show the user every Confirmed item as the reviewer wrote it, plus the pass SHA, range and report paths.

### 6. Loop

Each fix lands with the item's regression test. Push, then return to step 1 with fresh reviewers. Done means an incremental pass with no Confirmed items, followed by one fresh full pass that is also clean. A finding in the full pass restarts the loop.
