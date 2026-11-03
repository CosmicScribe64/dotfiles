"""Check a change walkthrough's code quotes against the diff.

usage: check_quotes.py WALK.md BASE [HEAD] [--repo PATH]

Quotes are checked against HEAD's committed files, so pass the PR head commit or
branch, not the literal HEAD. Omit HEAD to check the working tree against its
merge base with BASE. Every code block must sit directly under a
`[label](path#Lstart-Lend)` link, path relative to the walkthrough file, to
--repo or to the repository root. Quoted lines must be consecutive lines of
that range, apart from blank lines and gaps marked `...`, which may hide only
unchanged lines; the range starts and ends on quoted lines, and indentation may
shift only uniformly. In a diff block, `+` lines must be lines this change
added, other lines lines it did not, and `-` lines lines it removed near that
range. Link warnings flag quoted files whose checkout copy differs from HEAD,
so their links open the wrong lines. Also reports how many added production
lines (non-test, non-doc) are shown. Exit status 1 when any quote fails.
"""

import argparse
import os
import re
import subprocess
import sys
import urllib.parse

LINK = re.compile(r"\]\(<?([^)>#]+)#L(\d+)(?:-L(\d+))?>?\)")
# Fences may be indented inside list items; a longer fence can wrap a shorter one.
FENCE = re.compile(
    r"^(?P<indent>[ \t]*)(?P<fence>(?P<char>[`~])(?P=char){2,})(?P<info>[^\n]*)\n"
    r"(?P<body>.*?)^[ \t]*(?P=fence)(?P=char)*[ \t]*$",
    re.M | re.S,
)
HUNK = re.compile(r"^@@ -\d+(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
# Unlinked blocks of these languages are commands or output, not quotes.
UNQUOTED = {"mermaid", "console", "text", "output", "shell-session"}
NOT_PRODUCTION = re.compile(
    r"(_test\.|(^|/)test_|(^|/)tests?/|\.test\.|testdata|\.md$|\.json5?$|BUILD|\.bzl$|\.bazel$|\.params$)"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("walk")
    parser.add_argument("base")
    parser.add_argument("head", nargs="?", help="PR head commit or branch; omit to check the working tree")
    parser.add_argument("--repo", default=".")
    args = parser.parse_args()
    if args.head in ("HEAD", "@"):
        sys.exit("pass the PR head commit or branch, not HEAD: HEAD is whatever is checked out")

    def git(*command: str, required: bool = True) -> str | None:
        result = subprocess.run(
            ["git", "-C", args.repo, "-c", "core.quotePath=false", *command],
            capture_output=True, text=True, errors="surrogateescape",
        )
        if result.returncode:
            if required:
                sys.exit(f"git {' '.join(command)} failed: {result.stderr.strip()}")
            return None
        return result.stdout

    # The same output format whatever the user's diff config says.
    diff_options = ["diff", "--relative", "-U0", "-M", "--no-color", "--no-ext-diff", "--no-textconv",
                    "--src-prefix=a/", "--dst-prefix=b/"]
    if args.head:
        diff = git(*diff_options, f"{args.base}...{args.head}")
    else:
        diff = git(*diff_options, "--merge-base", args.base)

    added_text: dict[str, set[str]] = {}
    added_lines: dict[str, set[int]] = {}
    # Lines added by hunks that also removed lines: modified code, which reads best as a diff.
    modified_lines: dict[str, set[int]] = {}
    # Per hunk: the new-side lines around it and the lines it removed.
    removals: dict[str, list[tuple[int, int, set[str]]]] = {}
    new_files: set[str] = set()
    deleted_files: set[str] = set()
    old = current = ""
    in_header = False
    new_line = 0
    hunk_removed: set[str] = set()
    for line in diff.split("\n"):
        if line.startswith("diff "):
            in_header = True
        elif in_header and line.startswith("--- "):
            old = line[6:].rstrip("\t") if line.startswith("--- a/") else ""
        elif in_header and line.startswith("+++ "):
            # A deleted file's removed lines stay under its old path.
            current = line[6:].rstrip("\t") if line.startswith("+++ b/") else old
            if not old:
                new_files.add(current)
            if not line.startswith("+++ b/"):
                deleted_files.add(current)
        elif hunk := HUNK.match(line):
            in_header = False
            new_line = int(hunk[2])
            new_count = 1 if hunk[3] is None else int(hunk[3])
            hunk_removed = set()
            removals.setdefault(current, []).append((new_line, new_line + max(new_count, 1), hunk_removed))
            if hunk[1] != "0":
                modified_lines.setdefault(current, set()).update(range(new_line, new_line + new_count))
        elif not in_header and line.startswith("+"):
            added_text.setdefault(current, set()).add(line[1:].strip())
            added_lines.setdefault(current, set()).add(new_line)
            new_line += 1
        elif not in_header and line.startswith("-"):
            hunk_removed.add(line[1:].strip())

    text = open(args.walk, encoding="utf-8", errors="surrogateescape").read()
    failures = warnings = link_warnings = checked_blocks = 0
    quoted: set[str] = set()

    def fail(message: str) -> None:
        nonlocal failures
        failures += 1
        print(message)

    repo = os.path.realpath(args.repo)
    top = os.path.realpath(git("rev-parse", "--show-toplevel").strip())
    walk_dir = os.path.dirname(os.path.realpath(args.walk))

    def repo_path(link: str) -> str:
        link = urllib.parse.unquote(link.strip())
        candidates = [os.path.relpath(os.path.realpath(os.path.join(root, link)), repo) for root in (walk_dir, repo, top)]
        inside = [candidate for candidate in candidates if not candidate.startswith("..")]
        for candidate in inside:
            if candidate in removals or os.path.exists(os.path.join(repo, candidate)):
                return candidate
        return (inside or candidates)[0]

    def read_file(path: str) -> list[str] | None:
        try:
            return open(os.path.join(repo, path), encoding="utf-8", errors="surrogateescape").read().split("\n")
        except OSError:
            return None

    quoted_versions: dict[str, list[str] | None] = {}

    def quoted_version(path: str) -> list[str] | None:
        if path not in quoted_versions:
            if args.head:
                content = git("show", f"{args.head}:./{path}", required=False)
                quoted_versions[path] = None if content is None else content.split("\n")
            else:
                quoted_versions[path] = read_file(path)
        return quoted_versions[path]

    link_checked: set[str] = set()
    for block in FENCE.finditer(text):
        info = block["info"].split()
        language = info[0] if info else ""
        indent = len(block["indent"])
        body = [line[min(indent, len(line) - len(line.lstrip(" \t"))):] for line in block["body"].split("\n")]
        above = text[: block.start()].rstrip().split("\n")
        refs = LINK.findall(above[-1]) if above else []
        if not refs:
            if language not in UNQUOTED:
                fail(f"NO LINK above block starting: {next((l for l in body if l.strip()), '')[:70]!r}")
            continue
        checked_blocks += 1
        link, start, end = refs[-1]
        path = repo_path(link)
        start, end = int(start), int(end or start)
        if path.startswith(".."):
            fail(f"OUTSIDE REPO {link}: quote files under --repo")
            continue
        is_diff = language == "diff"
        quote: list[tuple[str, str, bool]] = []
        gap = False
        for line in body:
            mark = ""
            if is_diff and line[:1] in ("+", "-", " "):
                mark, line = line[:1], line[1:]
            core = line.rstrip()
            if core.strip() == "..." or (is_diff and core.startswith("@@")):
                gap = True
                continue
            if not core.strip():
                continue
            quoted.add(core.strip())
            if mark == "-":
                near = [hunk for hunk in removals.get(path, [])
                        if path in deleted_files or (hunk[0] <= end + 1 and hunk[1] >= start - 1)]
                if not any(core.strip() in hunk[2] for hunk in near):
                    fail(f"NOT REMOVED near {path}:{start}-{end}: {core.strip()[:90]}")
                continue
            quote.append((mark, core, gap))
            gap = False
        if not quote:
            continue
        lines = quoted_version(path)
        if lines is None:
            fail(f"MISSING FILE {path} in {args.head or 'the working tree'}")
            continue
        if args.head and path not in link_checked:
            link_checked.add(path)
            if read_file(path) != lines:
                link_warnings += 1
                print(f"LINK WARNING: the checkout's {path} differs from {args.head}, so its links open the wrong lines")
        window = lines[start - 1: end]
        added_here = added_lines.get(path, set())
        position = 0
        shifts: set[int] = set()
        matched: list[int] = []
        for index, (mark, core, gap_before) in enumerate(quote):
            target = core.strip()
            found = None
            for i in range(position, len(window)):
                if window[i].strip() == target:
                    found = i
                    break
                if window[i].strip() and index and not gap_before:
                    break
            if found is None:
                found = next((i for i in range(position, len(window)) if window[i].strip() == target), None)
                if found is None:
                    fail(f"NOT VERBATIM or out of order in {path}:{start}-{end}: {target[:90]}")
                    continue
                fail(f"SKIPPED LINES before {path}:{start + found}: mark the gap with `...`: {target[:90]}")
            if index and gap_before:
                hidden = [start + i for i in range(position, found) if start + i in added_here and window[i].strip()]
                if hidden:
                    fail(f"TRIMMED CHANGED LINE {path}:{hidden[0]}: `...` may hide only unchanged lines")
            number = start + found
            source = window[found].rstrip()
            shifts.add((len(source) - len(source.lstrip())) - (len(core) - len(core.lstrip())))
            if is_diff and mark == "+" and number not in added_here:
                fail(f"NOT ADDED by this change: {path}:{number}: {target[:90]}")
            if is_diff and mark != "+" and number in added_here:
                fail(f"NOT MARKED + but this change added {path}:{number}: {target[:90]}")
            matched.append(number)
            position = found + 1
        if len(shifts) > 1:
            fail(f"INDENT CHANGED in {path}:{start}-{end}: keep the file's relative indentation")
        nonblank = [start + i for i, line in enumerate(window) if line.strip()]
        if matched and nonblank and (nonblank[0] != matched[0] or nonblank[-1] != matched[-1]):
            fail(f"LOOSE RANGE {path}:{start}-{end}: start and end it on the first and last quoted lines")
        if not is_diff and path not in new_files and len(set(matched) & modified_lines.get(path, set())) >= 3:
            warnings += 1
            print(f"USE DIFF: {path}:{start}-{end} quotes lines this change modified")

    production = {
        line
        for path, lines in added_text.items()
        if not NOT_PRODUCTION.search(path)
        for line in lines
        if len(line) > 3 and not line.startswith(("//", "#", "*", "/*"))
    }
    if production and not checked_blocks:
        fail("NO QUOTES: the walkthrough quotes none of this change's code")
    shown_count = len(production & quoted)
    percent = 100 * shown_count // max(1, len(production))
    print(
        f"quote failures: {failures}; diff warnings: {warnings}; link warnings: {link_warnings}; "
        f"production lines shown: {shown_count}/{len(production)} ({percent}%)"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
