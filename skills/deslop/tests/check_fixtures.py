#!/usr/bin/env python3
"""Compare find_tells.py hit rates on human-written and AI-written fixtures.

Run before and after changing tells.json. Strong hits in human/ are false-positive
leads; a rule that fires often there should be narrowed or marked weak.

Usage: check_fixtures.py [--show human|ai]
"""

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
import find_tells  # noqa: E402


def check_regressions(scanner):
    def rules(text, ext=".md", allowed=None):
        hits, words = scanner.scan(text, ext, allowed=allowed)
        return {h["rule"] for h in hits}, words

    assert "citation-artifact" in rules("See [x](https://a.com/?utm_source=chatgpt.com) <mark>y</mark>.")[0]
    assert "ai-vocab" in rules("Use ```foo``` first.\n\nWe delve into the tapestry.\n")[0]
    assert not rules("````md\n```\nLet's delve into the tapestry.\n```\n````\n")[0]
    assert "ai-vocab" in rules("When a < b and we delve into c > d.\n")[0]
    assert "significance" in rules('A 15" screen.\nIt is a testament to design, "quoted" here.\n')[0]
    assert "step-comment" in rules("fn f<'a>(x: &'a str) {\n // Step 1: don't delve\n}\n", ".rs")[0]
    assert "step-comment" in rules("int n = 1'000; // Step 1: don't delve\n", ".cpp")[0]
    assert not rules('# Ignore "it is worth noting" and https://example.com/delve\n', ".py")[0]
    assert "long-sentence" not in rules("\n".join(f"x{i} = {i}  # sets item {i} in table" for i in range(8)), ".py")[0]
    assert "step-comment" in rules('"""Summary.\nStep 1: check cache.\nAdded retry.\n"""\n', ".py")[0]
    assert "bold-label-restate" not in rules("- **The fix:** Check the logs.\n")[0]
    assert "title-case-heading" not in rules("## Use GitHub Actions for CI\n")[0]
    assert "duplicate-sentence" not in rules(
        "Run `server-a` to start the primary local development service. "
        "Run `server-b` to start the primary local development service.\n")[0]
    assert "not-x-but-y" not in rules("If the file isn't found, it's created. It doesn't block. It is fast.\n")[0]
    assert "metaphor-noun-weak" not in rules("Keep the API surface and attack surface small.\n")[0]
    assert rules("One two three four.\nFive six.\n", ".md", allowed={2})[1] == 2
    assert "copula-dodge" in rules('#!/usr/bin/env python3\n"""This serves as a hub."""\nx = "seamless"\n', "")[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", choices=["human", "ai"], help="print strong hits for one corpus")
    args = ap.parse_args()
    data = json.loads((HERE.parent / "scripts" / "tells.json").read_text())
    scanner = find_tells.Scanner(data, include_weak=True, skip=set())
    check_regressions(scanner)
    for corpus in ("human", "ai"):
        words = strong = weak = 0
        by_rule = {}
        for f in sorted((HERE / "fixtures" / corpus).iterdir()):
            if f.suffix == ".md" and f.name == "SOURCES.md":
                continue
            hits, n = scanner.scan(f.read_text(), f.suffix.lower())
            words += n
            for h in hits:
                if h["weak"]:
                    weak += 1
                    continue
                strong += 1
                by_rule[h["rule"]] = by_rule.get(h["rule"], 0) + 1
                if args.show == corpus:
                    print(f"  {f.name}:{h['line']}: {h['rule']}: \"{h['match']}\"")
        top = ", ".join(f"{k} {v}" for k, v in sorted(by_rule.items(), key=lambda kv: -kv[1])[:8])
        print(f"{corpus:5}  {words:6} words  strong {1000 * strong / words:5.1f}/1k  "
              f"weak {1000 * weak / words:5.1f}/1k  top: {top or 'none'}")


if __name__ == "__main__":
    main()
