#!/usr/bin/env python3
"""Bookkeeping for a DeepWiki-style code wiki described by a wiki.json manifest.

Commands:
  stale  <wiki.json>              JSON report: pages to write, pages whose sources changed, uncovered files
  check  <wiki.json>              broken links and citations, out-of-range line ranges, structure errors (exit 1 if any)
  stamp  <wiki.json> SLUG...|--all  record HEAD (and any uncommitted source edits) as what each page was written against
  index  <wiki.json>              write index.md, the numbered page tree
"""

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

LINK = re.compile(r"\]\(([^)\s]+)\)")
LINE_RANGE = re.compile(r"L(\d+)(?:-L(\d+))?")
# `software/a/b.cpp:12-40`: a repo-root citation for wikis that forbid links out of the wiki.
PLAIN_CITE = re.compile(r"`([\w.+-]+(?:/[\w.+-]+)+):(\d+)(?:-(\d+))?`")


def load(manifest):
    path = Path(manifest).resolve()
    data = json.loads(path.read_text())
    repo = (path.parent / data["repo"]).resolve()
    return path, data, repo


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    ).stdout


def content_hash(repo, file):
    """Blob hash of the working-tree file, or None if it doesn't exist."""
    if not (repo / file).is_file():
        return None
    return git(repo, "hash-object", "--", file).strip()


def matches(file, patterns):
    """A pattern is a file path, a directory path (covers everything under it), or an fnmatch glob."""
    for pattern in patterns:
        pattern = pattern.rstrip("/")
        if file == pattern or file.startswith(pattern + "/") or fnmatch.fnmatchcase(file, pattern):
            return True
    return False


def cmd_stale(args):
    path, data, repo = load(args.manifest)
    untracked = git(repo, "ls-files", "--others", "--exclude-standard").splitlines()
    files = git(repo, "ls-files").splitlines() + untracked
    report = {"missing": [], "stale": {}, "empty_sources": [], "uncovered_count": 0, "uncovered": []}
    for page in data["pages"]:
        slug = page["slug"]
        if not any(matches(f, page["sources"]) for f in files):
            report["empty_sources"].append(slug)
        if not page.get("commit") or not (path.parent / f"{slug}.md").exists():
            report["missing"].append(slug)
            continue
        try:
            changed = git(repo, "diff", "--name-only", "--no-renames", page["commit"], "--").splitlines()
        except subprocess.CalledProcessError:
            report["stale"][slug] = [f"commit {page['commit']} not found; rewrite against HEAD"]
            continue
        stamped_dirty = page.get("dirty", {})
        hits = sorted(
            f for f in set(changed + untracked)
            if matches(f, page["sources"])
            and not (f in stamped_dirty and content_hash(repo, f) == stamped_dirty[f])
        )
        if hits:
            report["stale"][slug] = hits
    ignore = data.get("ignore", [])
    uncovered = [
        f for f in files
        if not matches(f, ignore) and not any(matches(f, p["sources"]) for p in data["pages"])
    ]
    report["uncovered_count"] = len(uncovered)
    report["uncovered"] = uncovered[: args.limit]
    print(json.dumps(report, indent=2))


def cmd_check(args):
    path, data, repo = load(args.manifest)
    root = path.parent
    problems = []
    slugs = [p["slug"] for p in data["pages"]]
    for slug in {s for s in slugs if slugs.count(s) > 1}:
        problems.append(f"wiki.json: duplicate slug {slug}")
    for page in data["pages"]:
        if page.get("parent") and page["parent"] not in slugs:
            problems.append(f"wiki.json: {page['slug']} has unknown parent {page['parent']}")
        if not page.get("sources"):
            problems.append(f"wiki.json: {page['slug']} has no sources")
    for extra in sorted(root.glob("*.md")):
        if extra.stem not in slugs and extra.name != "index.md":
            problems.append(f"{extra.name}: page not in wiki.json")
    line_counts = {}

    def check_range(where, label, resolved, start, end):
        if resolved not in line_counts:
            line_counts[resolved] = len(resolved.read_bytes().splitlines())
        if not 1 <= start <= end <= line_counts[resolved]:
            problems.append(f"{where}: {label} outside 1-{line_counts[resolved]}")

    for slug in slugs:
        page = root / f"{slug}.md"
        if not page.exists():
            problems.append(f"{slug}.md: missing")
            continue
        text = page.read_text()
        if "Sources:" not in text:
            problems.append(f"{slug}.md: no Sources: lines")
        for number, line in enumerate(text.splitlines(), 1):
            where = f"{slug}.md:{number}"
            for match in LINK.finditer(line):
                target = match.group(1)
                if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", target):
                    continue
                file_part, _, fragment = target.partition("#")
                if not file_part:
                    continue
                resolved = (page.parent / unquote(file_part)).resolve()
                if not resolved.exists():
                    problems.append(f"{where}: broken link {target}")
                    continue
                lines = LINE_RANGE.fullmatch(fragment)
                if lines and resolved.is_file():
                    check_range(where, target, resolved, int(lines.group(1)), int(lines.group(2) or lines.group(1)))
            for match in PLAIN_CITE.finditer(line):
                file_part, start, end = match.groups()
                resolved = repo / file_part
                if not resolved.is_file():
                    problems.append(f"{where}: cited file not in repo: {file_part}")
                    continue
                check_range(where, match.group(0), resolved, int(start), int(end or start))
    for problem in problems:
        print(problem)
    print(f"{len(problems)} problem(s)", file=sys.stderr)
    return 1 if problems else 0


def cmd_stamp(args):
    path, data, repo = load(args.manifest)
    head = git(repo, "rev-parse", "HEAD").strip()
    dirty = [line[3:] for line in git(repo, "status", "--porcelain", "--no-renames").splitlines()]
    wanted = set(args.slugs)
    known = {p["slug"] for p in data["pages"]}
    unknown = wanted - known
    if unknown:
        sys.exit(f"unknown slug(s): {', '.join(sorted(unknown))}")
    for page in data["pages"]:
        if args.all or page["slug"] in wanted:
            page["commit"] = head
            touched = [f for f in dirty if matches(f, page["sources"])]
            if touched:
                # The page describes these uncommitted edits; stale ignores them until they change again.
                page["dirty"] = {f: content_hash(repo, f) for f in touched}
                print(f"note: {page['slug']} written against uncommitted {', '.join(touched)}", file=sys.stderr)
            else:
                page.pop("dirty", None)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"stamped {head[:12]}")


def cmd_index(args):
    path, data, repo = load(args.manifest)
    children = {}
    for page in data["pages"]:
        children.setdefault(page.get("parent"), []).append(page)
    lines = [
        f"# {data.get('name') or repo.name}",
        "",
        f"Code wiki for `{data['repo']}`. Structure lives in [wiki.json](wiki.json).",
        "",
    ]

    def walk(parent, prefix, depth):
        for i, page in enumerate(children.get(parent, []), 1):
            number = f"{prefix}{i}"
            lines.append(f"{'  ' * depth}- {number} [{page['title']}]({page['slug']}.md): {page['purpose']}")
            walk(page["slug"], number + ".", depth + 1)

    walk(None, "", 0)
    (path.parent / "index.md").write_text("\n".join(lines) + "\n")
    print(f"wrote {path.parent / 'index.md'}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    stale = sub.add_parser("stale")
    stale.add_argument("manifest")
    stale.add_argument("--limit", type=int, default=100, help="max uncovered files listed")
    sub.add_parser("check").add_argument("manifest")
    stamp = sub.add_parser("stamp")
    stamp.add_argument("manifest")
    stamp.add_argument("slugs", nargs="*")
    stamp.add_argument("--all", action="store_true")
    sub.add_parser("index").add_argument("manifest")
    args = parser.parse_args()
    if args.command == "stamp" and not (args.slugs or args.all):
        parser.error("stamp needs slugs or --all")
    commands = {"stale": cmd_stale, "check": cmd_check, "stamp": cmd_stamp, "index": cmd_index}
    sys.exit(commands[args.command](args) or 0)


if __name__ == "__main__":
    main()
