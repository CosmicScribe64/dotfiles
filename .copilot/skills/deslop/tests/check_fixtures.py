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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", choices=["human", "ai"], help="print strong hits for one corpus")
    args = ap.parse_args()
    data = json.loads((HERE.parent / "scripts" / "tells.json").read_text())
    scanner = find_tells.Scanner(data, include_weak=True, skip=set())
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
