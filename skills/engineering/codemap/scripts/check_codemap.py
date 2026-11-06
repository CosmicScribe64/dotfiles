#!/usr/bin/env python3
"""Check a codemap against the code it maps, or list its nodes as file:line jump targets.

  check_codemap.py MAP.md          verify every node's snippet, ref and map node (exit 1 on problems)
  check_codemap.py MAP.md --list   print `path:line: [1a] title` for each node (clickable in a terminal)

A located node is a list item `- **1a** [label](relative/path#L91) Title`, followed by a line
holding its code in backticks. The snippet must appear in that source line; a trailing `…` or
`...` marks a truncated snippet and only the part before it is compared.
"""

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import unquote

NODE = re.compile(r"^\s*- \*\*(\d+[a-z])\*\* \[[^\]]*\]\(([^)#\s]+)#L(\d+)\)\s*(.*)$")
SNIPPET = re.compile(r"^\s*(`+)(.*?)\1\s*$")
REF = re.compile(r"\[(\d+[a-z])\](?!\()")
MERMAID_NODE = re.compile(r"\bn(\d+[a-z])\b")


def parse(path):
    lines = path.read_text().splitlines()
    nodes, problems = {}, []
    for i, line in enumerate(lines):
        match = NODE.match(line)
        if not match:
            continue
        node_id, target, line_no, title = match.groups()
        snippet = SNIPPET.match(lines[i + 1]) if i + 1 < len(lines) else None
        if node_id in nodes:
            problems.append(f"{path.name}:{i + 1}: duplicate node {node_id}")
        nodes[node_id] = {
            "file": (path.parent / unquote(target)).resolve(),
            "line": int(line_no),
            "title": title.strip(),
            "snippet": snippet.group(2) if snippet else None,
            "at": i + 1,
        }
    return lines, nodes, problems


def mermaid_errors(path, blocks):
    """Render each block with mmdc; return parse errors, or a note when mmdc is absent."""
    mmdc = shutil.which("mmdc")
    if not mmdc:
        print("note: mmdc not found, Mermaid syntax not checked", file=sys.stderr)
        return []
    errors = []
    # Snap-packaged mmdc can't read /tmp, so render beside the codemap.
    with tempfile.TemporaryDirectory(dir=path.parent) as tmp:
        for i, block in enumerate(blocks, 1):
            source = Path(tmp) / f"map{i}.mmd"
            source.write_text(block)
            run = subprocess.run(
                [mmdc, "-i", str(source), "-o", str(source.with_suffix(".svg"))],
                capture_output=True, text=True, timeout=180,
            )
            if run.returncode != 0:
                detail = next((l for l in (run.stdout + run.stderr).splitlines() if "rror" in l), "mmdc failed")
                errors.append(f"{path.name}: mermaid block {i}: {detail.strip()}")
    return errors


def check(path):
    lines, nodes, problems = parse(path)
    if not nodes:
        problems.append(f"{path.name}: no located nodes found")
    for node_id, node in nodes.items():
        where = f"{path.name}:{node['at']}: {node_id}"
        if node["snippet"] is None:
            problems.append(f"{where}: no backticked snippet on the next line")
            continue
        if not node["file"].is_file():
            problems.append(f"{where}: missing file {node['file']}")
            continue
        source = node["file"].read_text(errors="replace").splitlines()
        if not 1 <= node["line"] <= len(source):
            problems.append(f"{where}: line {node['line']} outside 1-{len(source)}")
            continue
        want = re.split(r"\s*(?:…|\.\.\.)$", node["snippet"].strip())[0]
        have = source[node["line"] - 1]
        if want not in have:
            problems.append(f"{where}: snippet not on line {node['line']}: {have.strip()!r}")
    text = "\n".join(lines)
    for ref in sorted(set(REF.findall(text)) - set(nodes)):
        problems.append(f"{path.name}: [{ref}] refers to no node")
    blocks = re.findall(r"```mermaid\n(.*?)```", text, re.S)
    mermaid = "\n".join(blocks)
    if not mermaid:
        problems.append(f"{path.name}: no mermaid map")
    else:
        problems.extend(mermaid_errors(path, blocks))
        drawn = set(MERMAID_NODE.findall(mermaid))
        for node_id in sorted(drawn - set(nodes)):
            problems.append(f"{path.name}: map node n{node_id} has no matching node")
        for node_id in sorted(set(nodes) - drawn):
            problems.append(f"{path.name}: node {node_id} missing from the map")
    for problem in problems:
        print(problem)
    print(f"{len(nodes)} node(s), {len(problems)} problem(s)", file=sys.stderr)
    return 1 if problems else 0


def list_nodes(path):
    _, nodes, _ = parse(path)
    for node_id, node in nodes.items():
        print(f"{node['file']}:{node['line']}: [{node_id}] {node['title']}")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("codemap", type=Path)
    parser.add_argument("--list", action="store_true", help="print nodes as path:line jump targets")
    args = parser.parse_args()
    sys.exit(list_nodes(args.codemap) if args.list else check(args.codemap))


if __name__ == "__main__":
    main()
