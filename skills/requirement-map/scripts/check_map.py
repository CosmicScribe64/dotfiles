#!/usr/bin/env python3
"""Check or initialize a requirement-map CSV against git diff and a wiki page.

usage: check_map.py MAP.csv BASE [HEAD] [--repo PATH] [--wiki-page WIKI_REL_PATH]
                    [--no-wiki] [--init-csv] [--link-style {chat,wiki}]

MAP.csv columns: file,requirement,kind,added,removed[,hunk]
  - kind is 'prod' or 'test' (consistent per file)
  - added and removed are non-negative integers summing per file to git diff --numstat
  - optional hunk column (populated by --init-csv) pins rows to exact git diff -U0 hunks

When --wiki-page is given (required if <repo>/wiki exists unless --no-wiki is set), every
requirement ID in MAP.csv except NONE must have a heading `### <ID>: <title>` under the
page's `## Requirements` section (`### <ID> <title>` is also accepted there). Without that
section, any `<ID>: <title>` heading counts. Prints the reconciled summary table with links.
Exit status 1 on any mismatch or missing requirement heading.
"""

from __future__ import annotations

import argparse
import collections
import csv
from pathlib import Path
import re
import subprocess
import sys

# Group 3 is the separator: under ## Requirements a bare space is accepted (`### R1 Summary`).
HEADING_RE = re.compile(r"^(#{2,6})\s+([A-Za-z0-9_.-]+)(\s*[:—–]\s*|\s+-\s+|\s+|$)(.*?)\s*$")
BARE_ID_RE = re.compile(r"^(?:[A-Z0-9][A-Z0-9_.-]*|.*[0-9].*)$")
SECTION_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
HUNK_RE = re.compile(r"^@@\s+(-\d+(?:,\d+)?\s+\+\d+(?:,\d+)?)\s+@@")
TEST_PATH_RE = re.compile(
    r"(?:^|/)(?:tests?|__tests__|specs?|testdata|fixtures)(?:/|$)"
    r"|(?:^|/)(?:test_[^/]+|[^/]+_(?:test|spec)\.[^/]+|[^/]+\.(?:test|spec)\.[^/]+)$"
)


def slugify(heading_text: str) -> str:
    clean = re.sub(r"[^\w\s-]", "", heading_text.lower())
    return re.sub(r"\s+", "-", clean.strip())


def infer_kind(path: str) -> str:
    return "test" if TEST_PATH_RE.search(path) else "prod"


def resolve_diff_args(base: str, head: str | None) -> list[str]:
    if ".." in base:
        if head and not base.endswith(f".{head}"):
            sys.stderr.write(
                f"ERROR: base '{base}' already contains '..'; omit HEAD '{head}'\n"
            )
            sys.exit(2)
        return [base]
    if head is None:
        return [base]
    if head in ("--staged", "--cached"):
        return [head, base]
    return [f"{base}...{head}"]


def git_numstat(repo: Path, diff_args: list[str]) -> dict[str, tuple[int, int]]:
    proc = subprocess.run(
        ["git", "-C", str(repo), "diff", "--numstat", "-z", "--no-renames", *diff_args],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr or f"git diff --numstat failed ({proc.returncode})\n")
        sys.exit(2)
    out: dict[str, tuple[int, int]] = {}
    for entry in proc.stdout.split("\0"):
        if not entry:
            continue
        parts = entry.split("\t", 2)
        if len(parts) != 3:
            continue
        add_s, rem_s, path = parts
        added = 0 if add_s == "-" else int(add_s)
        removed = 0 if rem_s == "-" else int(rem_s)
        out[path] = (added, removed)
    return out


def git_hunks(
    repo: Path, diff_args: list[str], numstat: dict[str, tuple[int, int]]
) -> dict[str, list[tuple[str, int, int]]]:
    proc = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "core.quotePath=false",
            "diff",
            "-U0",
            "--no-renames",
            *diff_args,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr or f"git diff -U0 failed ({proc.returncode})\n")
        sys.exit(2)

    hunks_by_file: dict[str, list[tuple[str, int, int]]] = collections.defaultdict(list)
    minus_path = ""
    current_file = ""
    current_hunk = ""
    hunk_add = 0
    hunk_rem = 0

    def flush() -> None:
        nonlocal current_hunk, hunk_add, hunk_rem
        if current_file and current_hunk:
            hunks_by_file[current_file].append((current_hunk, hunk_add, hunk_rem))
        current_hunk = ""
        hunk_add = 0
        hunk_rem = 0

    for line in proc.stdout.splitlines():
        if line.startswith("diff "):
            flush()
            minus_path = ""
            current_file = ""
        elif line.startswith("--- ") and not current_hunk:
            minus_path = line[6:] if line.startswith("--- a/") else ""
        elif line.startswith("+++ ") and not current_hunk:
            plus_path = line[6:] if line.startswith("+++ b/") else ""
            current_file = plus_path or minus_path
        elif line.startswith("@@ "):
            flush()
            m = HUNK_RE.match(line)
            current_hunk = m.group(1) if m else line.split("@@")[1].strip()
        elif current_hunk:
            if line.startswith("+"):
                hunk_add += 1
            elif line.startswith("-"):
                hunk_rem += 1
    flush()

    for path, (exp_a, exp_r) in numstat.items():
        if path not in hunks_by_file:
            hunks_by_file[path].append(("", exp_a, exp_r))
    return hunks_by_file


def parse_wiki_headings(wiki_file: Path) -> tuple[dict[str, tuple[int, str, str]], bool]:
    """Return (req_id -> (line_no, title, anchor_slug), had_requirements_section)."""
    lines = wiki_file.read_text(encoding="utf-8").splitlines()
    all_reqs: dict[str, tuple[int, str, str]] = {}
    section_reqs: dict[str, tuple[int, str, str]] = {}
    in_fence = ""
    req_section_level = 0
    had_req_section = False

    for lineno, raw in enumerate(lines, 1):
        fence_m = FENCE_RE.match(raw)
        if fence_m:
            marker = fence_m.group(1)[:3]
            if not in_fence:
                in_fence = marker
            elif in_fence == marker:
                in_fence = ""
            continue
        if in_fence:
            continue

        sec_m = SECTION_RE.match(raw)
        if sec_m:
            level = len(sec_m.group(1))
            heading_title = sec_m.group(2).strip().lower()
            if heading_title == "requirements":
                req_section_level = level
                had_req_section = True
                continue
            if req_section_level and level <= req_section_level:
                req_section_level = 0

        m = HEADING_RE.match(raw)
        if not m:
            continue
        level = len(m.group(1))
        req_id = m.group(2)
        has_delimiter = bool(m.group(3).strip())
        title = m.group(4).strip()
        full = raw.lstrip("#").strip()
        entry = (lineno, title, slugify(full))
        if has_delimiter:
            all_reqs[req_id] = entry
        if req_section_level and level > req_section_level:
            if has_delimiter or (
                level == req_section_level + 1 and BARE_ID_RE.match(req_id)
            ):
                section_reqs[req_id] = entry

    return (section_reqs if had_req_section else all_reqs), had_req_section


def write_initial_csv(
    map_csv: Path,
    numstat: dict[str, tuple[int, int]],
    hunks_by_file: dict[str, list[tuple[str, int, int]]],
) -> int:
    fieldnames = ["file", "requirement", "kind", "added", "removed", "hunk"]
    handle = (
        sys.stdout
        if str(map_csv) == "-"
        else map_csv.open("w", encoding="utf-8", newline="")
    )
    with handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for path in sorted(numstat):
            kind = infer_kind(path)
            for hunk_range, added, removed in hunks_by_file[path]:
                writer.writerow(
                    {
                        "file": path,
                        "requirement": "TODO",
                        "kind": kind,
                        "added": added,
                        "removed": removed,
                        "hunk": hunk_range,
                    }
                )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("map_csv", type=Path)
    parser.add_argument("base")
    parser.add_argument("head", nargs="?", default=None)
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--wiki-page", default=None)
    parser.add_argument("--no-wiki", action="store_true")
    parser.add_argument("--init-csv", action="store_true")
    parser.add_argument("--link-style", choices=("chat", "wiki"), default="chat")
    args = parser.parse_args()

    repo = args.repo.resolve()
    diff_args = resolve_diff_args(args.base, args.head)
    numstat = git_numstat(repo, diff_args)
    hunks_by_file = git_hunks(repo, diff_args, numstat)

    if args.init_csv:
        return write_initial_csv(args.map_csv, numstat, hunks_by_file)

    errors: list[str] = []

    if not args.map_csv.is_file():
        print(f"ERROR: CSV not found: {args.map_csv}", file=sys.stderr)
        return 1

    per_file: dict[str, list[int]] = collections.defaultdict(lambda: [0, 0])
    file_kinds: dict[str, set[str]] = collections.defaultdict(set)
    file_row_counts: dict[str, int] = collections.defaultdict(int)
    file_missing_hunk_lines: dict[str, list[int]] = collections.defaultdict(list)
    per_hunk: dict[tuple[str, str], list[int]] = collections.defaultdict(lambda: [0, 0])
    per_req: dict[str, dict[str, int]] = collections.defaultdict(
        lambda: {"prod_a": 0, "test_a": 0, "rem": 0}
    )
    by_file_req: dict[tuple[str, str, str], list[int]] = collections.defaultdict(
        lambda: [0, 0]
    )

    with args.map_csv.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        expected_cols = {"file", "requirement", "kind", "added", "removed"}
        if not reader.fieldnames or not (set(reader.fieldnames) >= expected_cols):
            print(
                f"ERROR: CSV must have columns {sorted(expected_cols)}, got {reader.fieldnames}",
                file=sys.stderr,
            )
            return 1
        for idx, row in enumerate(reader, 2):
            f = (row.get("file") or "").strip()
            req = (row.get("requirement") or "").strip()
            kind = (row.get("kind") or "").strip()
            hunk = (row.get("hunk") or "").strip()
            try:
                added = int(row["added"])
                removed = int(row["removed"])
            except (TypeError, ValueError):
                errors.append(f"line {idx}: non-integer added/removed in {row}")
                continue
            if not f or not req:
                errors.append(f"line {idx}: empty file or requirement in {row}")
                continue
            if req == "TODO":
                errors.append(f"line {idx}: unassigned requirement 'TODO' for {f}")
                continue
            if kind not in ("prod", "test"):
                errors.append(f"line {idx}: kind must be 'prod' or 'test', got '{kind}'")
                continue
            if added < 0 or removed < 0:
                errors.append(f"line {idx}: negative counts in {row}")
                continue
            per_file[f][0] += added
            per_file[f][1] += removed
            file_kinds[f].add(kind)
            file_row_counts[f] += 1
            if hunk:
                per_hunk[(f, hunk)][0] += added
                per_hunk[(f, hunk)][1] += removed
            else:
                file_missing_hunk_lines[f].append(idx)
            bucket = per_req[req]
            if kind == "prod":
                bucket["prod_a"] += added
            else:
                bucket["test_a"] += added
            bucket["rem"] += removed
            agg = by_file_req[(f, req, kind)]
            agg[0] += added
            agg[1] += removed

    for f, kinds in sorted(file_kinds.items()):
        if len(kinds) > 1:
            errors.append(f"mixed kind for {f}: rows have both 'prod' and 'test'")

    expected_hunks = {
        (f, h): (a, r)
        for f, hlist in hunks_by_file.items()
        for h, a, r in hlist
        if h
    }
    files_with_hunks = {f for f, _ in expected_hunks}
    files_using_hunks = {f for f, _ in per_hunk}
    for f, count in sorted(file_row_counts.items()):
        if f in files_with_hunks and (count > 1 or f in files_using_hunks):
            for line_no in file_missing_hunk_lines.get(f, []):
                errors.append(
                    f"line {line_no}: missing hunk range for multi-row file {f}"
                )
            for h, exp_a, exp_r in hunks_by_file[f]:
                if h and (f, h) not in per_hunk:
                    errors.append(
                        f"missing hunk for {f} @@ {h} @@ (+{exp_a}/-{exp_r})"
                    )
    for (f, hunk), (got_a, got_r) in sorted(per_hunk.items()):
        if (f, hunk) not in expected_hunks:
            errors.append(f"unknown hunk '{hunk}' for {f}")
            continue
        exp_a, exp_r = expected_hunks[(f, hunk)]
        if (got_a, got_r) != (exp_a, exp_r):
            errors.append(
                f"hunk mismatch for {f} @@ {hunk} @@: CSV has +{got_a}/-{got_r}, diff has +{exp_a}/-{exp_r}"
            )

    for f, (exp_a, exp_r) in sorted(numstat.items()):
        if f not in per_file:
            errors.append(f"missing file from numstat: {f} (+{exp_a}/-{exp_r})")
            continue
        got_a, got_r = per_file[f]
        if (got_a, got_r) != (exp_a, exp_r):
            errors.append(
                f"count mismatch for {f}: CSV has +{got_a}/-{got_r}, numstat has +{exp_a}/-{exp_r}"
            )
    for f in sorted(set(per_file) - set(numstat)):
        got_a, got_r = per_file[f]
        errors.append(f"extra file not in numstat: {f} (+{got_a}/-{got_r})")

    wiki_reqs: dict[str, tuple[int, str, str]] = {}
    had_req_section = False
    wiki_rel = args.wiki_page
    if not args.no_wiki and (wiki_rel or (repo / "wiki").is_dir()):
        if not wiki_rel:
            errors.append("repo has wiki/; pass --wiki-page wiki/<path>.md (or --no-wiki)")
        else:
            wiki_candidate = Path(wiki_rel)
            wiki_file = (
                wiki_candidate.resolve()
                if wiki_candidate.is_absolute()
                else (repo / wiki_candidate).resolve()
            )
            if not wiki_file.is_file():
                errors.append(f"wiki page not found: {wiki_rel}")
            else:
                try:
                    wiki_rel = wiki_file.relative_to(repo).as_posix()
                except ValueError:
                    wiki_rel = wiki_file.as_posix()
                wiki_reqs, had_req_section = parse_wiki_headings(wiki_file)
                for req in sorted(per_req):
                    if req == "NONE":
                        continue
                    if req not in wiki_reqs:
                        errors.append(
                            f"requirement '{req}' has no '### {req}: <title>' heading in {wiki_rel}"
                        )

    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    ordered = sorted(
        per_req.items(),
        key=lambda kv: (
            kv[0] == "NONE",
            -(kv[1]["prod_a"] + kv[1]["test_a"]),
            -kv[1]["rem"],
            kv[0],
        ),
    )
    tot_prod = sum(v["prod_a"] for _, v in ordered)
    tot_test = sum(v["test_a"] for _, v in ordered)
    tot_rem = sum(v["rem"] for _, v in ordered)
    tot_add = tot_prod + tot_test

    print("| Requirement | Production | Tests | Total added | Removed |")
    print("|---|---|---|---|---|")
    for req, v in ordered:
        total_a = v["prod_a"] + v["test_a"]
        if req in wiki_reqs and wiki_rel:
            lineno, title, slug = wiki_reqs[req]
            suffix = f" {title}" if title else ""
            target = f"#{slug}" if args.link_style == "wiki" else f"{wiki_rel}#L{lineno}"
            label = f"[**{req}**]({target}){suffix}"
        else:
            label = f"**{req}**"
        print(f"| {label} | {v['prod_a']} | {v['test_a']} | **{total_a}** | {v['rem']} |")
    print(f"| **Total** | {tot_prod} | {tot_test} | **{tot_add}** | {tot_rem} |")
    print()
    print("Top contributors:")
    ranked_contributors = sorted(
        (
            (added + removed, added, removed, f, req, kind)
            for (f, req, kind), (added, removed) in by_file_req.items()
        ),
        reverse=True,
    )
    for _impact, added, removed, f, req, kind in ranked_contributors[:5]:
        print(f"- {f} ({req}, {kind}): +{added}/-{removed}")

    if had_req_section:
        unused = sorted(set(wiki_reqs) - set(per_req))
        if unused:
            print(f"\nUnmapped wiki requirements (0 lines in diff): {', '.join(unused)}")

    print(
        f"\nOK: {len(numstat)} files, +{tot_add}/-{tot_rem} reconciled, "
        f"{len(per_req) - (1 if 'NONE' in per_req else 0)} requirements verified."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
