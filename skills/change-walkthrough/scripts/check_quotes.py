"""Check a change walkthrough's code quotes against the checkout and the base.

usage: check_quotes.py WALK.md BASE HEAD [--repo PATH]

Every code block must sit directly under a `[label](path#Lstart-Lend)` link.
Unchanged and added lines must appear in that range of the checkout; removed
(`-`) lines in a diff block must appear in the BASE version of the file.
Also reports how many added production lines (non-test, non-doc) are shown.
Exit status 1 when any quote fails.
"""

import argparse
import re
import subprocess
import sys

LINK = re.compile(r"\]\(([^)#]+)#L(\d+)(?:-L(\d+))?\)")
NOT_PRODUCTION = re.compile(
    r"(_test\.|test_|/tests?/|\.test\.|testdata|\.md$|\.json5?$|BUILD|\.bzl$|\.bazel$|\.proto$|\.params$|\.ya?ml$)"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("walk")
    parser.add_argument("base")
    parser.add_argument("head")
    parser.add_argument("--repo", default=".")
    args = parser.parse_args()

    def git(*command: str) -> str:
        return subprocess.run(
            ["git", "-C", args.repo, *command], capture_output=True, text=True, check=False
        ).stdout

    text = open(args.walk, encoding="utf-8").read()
    parts = re.split(r"(```[^\n]*\n.*?```)", text, flags=re.S)
    existed = set(git("ls-tree", "-r", "--name-only", args.base).splitlines())
    # Added lines from hunks that also removed lines: modified code, which reads best as a diff.
    added_by_file: dict[str, set[str]] = {}
    current = ""
    hunk_added: list[str] = []
    hunk_removed = False

    def close_hunk() -> None:
        if current and hunk_removed:
            added_by_file.setdefault(current, set()).update(hunk_added)

    for line in git("diff", "-U0", f"{args.base}...{args.head}").splitlines():
        if line.startswith(("+++ ", "@@", "diff ")):
            close_hunk()
            hunk_added, hunk_removed = [], False
            if line.startswith("+++ "):
                current = line[6:] if line.startswith("+++ b/") else ""
        elif line.startswith("+") and current:
            hunk_added.append(line[1:].strip())
        elif line.startswith("-") and not line.startswith("---"):
            hunk_removed = True
    close_hunk()
    failures = 0
    warnings = 0
    quoted: set[str] = set()
    base_files: dict[str, set[str]] = {}
    for index, part in enumerate(parts):
        if not part.startswith("```"):
            continue
        language = part.split("\n", 1)[0][3:].strip()
        above = parts[index - 1].rstrip().splitlines()
        refs = LINK.findall(above[-1]) if above else []
        if not refs:
            failures += 1
            print(f"NO LINK above block starting: {part.splitlines()[1][:70]!r}")
            continue
        path, start, end = refs[-1]
        start, end = int(start), int(end or start)
        try:
            window = open(f"{args.repo}/{path}", encoding="utf-8").read().splitlines()[start - 1: end]
        except OSError:
            failures += 1
            print(f"MISSING FILE {path}")
            continue
        window = [line.strip() for line in window]
        if language != "diff" and path in existed:
            body = {l.strip() for l in part.splitlines()[1:-1]}
            if len(body & added_by_file.get(path, set())) >= 3:
                warnings += 1
                print(f"USE DIFF: {path}:{start}-{end} quotes lines this change modified")
        for line in part.splitlines()[1:-1]:
            removed = False
            if language == "diff" and line[:1] in "+- ":
                removed, line = line[:1] == "-", line[1:]
            core = re.sub(r"\s*(//|#) was:.*$", "", line).strip()
            if not core or core == "...":
                continue
            quoted.add(core)
            if removed:
                if path not in base_files:
                    base_files[path] = {l.strip() for l in git("show", f"{args.base}:{path}").splitlines()}
                ok = core in base_files[path]
            else:
                ok = core in window
            if not ok:
                failures += 1
                side = "base" if removed else f"{path}:{start}-{end}"
                print(f"NOT VERBATIM in {side}: {core[:90]}")

    added: set[str] = set()
    current = ""
    for line in git("diff", "-U0", f"{args.base}...{args.head}").splitlines():
        if line.startswith("+++ "):
            current = line[6:] if line.startswith("+++ b/") else ""
        elif line.startswith("+") and current and not NOT_PRODUCTION.search(current):
            core = line[1:].strip()
            if len(core) > 3 and not core.startswith(("//", "#", "*", "/*")):
                added.add(core)
    shown = len(added & quoted)
    percent = 100 * shown // max(1, len(added))
    print(
        f"quote failures: {failures}; diff warnings: {warnings}; "
        f"production lines shown: {shown}/{len(added)} ({percent}%)"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
