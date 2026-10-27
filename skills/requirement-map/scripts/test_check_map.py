#!/usr/bin/env python3
"""Self-tests for check_map.py --carry-from and --link-style pr. Run: python3 test_check_map.py"""

import csv
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("check_map.py")


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *args],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


def run(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args, "--repo", str(repo), "--no-wiki"],
        capture_output=True, text=True, check=False,
    )


class CheckMapTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        git(self.repo, "init", "-q")
        (self.repo / "a.txt").write_text("".join(f"line {i}\n" for i in range(40)))
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "base")
        self.base = git(self.repo, "rev-parse", "HEAD")
        lines = (self.repo / "a.txt").read_text().splitlines(keepends=True)
        lines[2:2] = ["new A\n", "new B\n", "new C\n"]
        (self.repo / "a.txt").write_text("".join(lines))
        git(self.repo, "commit", "-qam", "head1")
        self.head1 = git(self.repo, "rev-parse", "HEAD")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write_split_map(self) -> Path:
        """Map head1's single 3-line hunk split across R1 (2 lines) and R2 (1 line)."""
        seed = self.repo / "seed.csv"
        self.assertEqual(run(self.repo, str(seed), self.base, self.head1, "--init-csv").returncode, 0)
        [row] = list(csv.DictReader(seed.read_text().splitlines()))
        old = self.repo / "old.csv"
        with old.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=row.keys())
            writer.writeheader()
            writer.writerow({**row, "requirement": "R1", "added": "2"})
            writer.writerow({**row, "requirement": "R2", "added": "1"})
        return old

    def test_carry_keeps_split_rows_and_marks_only_new_hunks(self) -> None:
        old = self.write_split_map()
        lines = (self.repo / "a.txt").read_text().splitlines(keepends=True)
        lines.insert(30, "late\n")
        (self.repo / "a.txt").write_text("".join(lines))
        git(self.repo, "commit", "-qam", "head2")
        new = self.repo / "new.csv"
        result = run(self.repo, str(new), self.base, "HEAD", "--init-csv", "--carry-from", str(old))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("carried 1 hunks", result.stderr)
        reqs = sorted(r["requirement"] for r in csv.DictReader(new.read_text().splitlines()))
        self.assertEqual(reqs, ["R1", "R2", "TODO"])

    def test_pr_style_has_plain_names_and_no_links_or_ids(self) -> None:
        old = self.write_split_map()
        rows = list(csv.DictReader(old.read_text().splitlines()))
        rows[1]["requirement"] = "NONE"
        with old.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        names = self.repo / "names.csv"
        names.write_text("id,name\nR1,Per-scan summary\nNONE,Unrelated: stale test expectation\n")
        result = run(self.repo, str(old), self.base, self.head1, "--link-style", "pr", "--names", str(names))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("| Per-scan summary | 2 |", result.stdout)
        self.assertIn("| Unrelated: stale test expectation |", result.stdout)
        self.assertIn(f"`{self.head1[:7]}", result.stdout)
        self.assertNotIn("](", result.stdout)
        self.assertNotIn("R1", result.stdout)


if __name__ == "__main__":
    unittest.main()
