#!/usr/bin/env python3
"""Self-tests for check_quotes.py. Run: python3 test_check_quotes.py"""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("check_quotes.py")
FENCE = "`" * 3
H = ("base", "head")


def sh(*cmd: str, cwd: str) -> None:
    subprocess.run(cmd, cwd=cwd, check=True, capture_output=True)


def commit(repo: str, files: dict[str, str], delete=(), rename=()) -> None:
    for old, new in rename:
        sh("git", "mv", old, new, cwd=repo)
    for name in delete:
        sh("git", "rm", "-q", name, cwd=repo)
    for name, body in files.items():
        os.makedirs(os.path.dirname(os.path.join(repo, name)) or repo, exist_ok=True)
        Path(repo, name).write_text(body)
    sh("git", "add", "-A", cwd=repo)
    sh("git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "c", cwd=repo)


def block(link: str, language: str, *lines: str, fence: str = FENCE) -> str:
    return f"{link}\n{fence}{language}\n" + "\n".join(lines) + f"\n{fence}\n\n"


GOOD = (
    block("[app.py:1-4](app.py#L1-L4)", "diff", " def f():", "-    x = 1", "+    x = 2", "+    y = x + 1",
          "-    return x", "+    return y")
    + block("[gone.py:1-2](gone.py#L1-L2)", "diff", "-def old():", "-    return 0")
    + block("[moved.py:5](moved.py#L5)", "diff", "-e = 5", "+e = 50")
    + block("[q.sql:1-2](q.sql#L1-L2)", "diff", " -- keep", "--- drop me", " select 1;")
    + block("[doc.md:1-4](doc.md#L1-L4)", "markdown", "intro", FENCE, "code", FENCE, fence="````")
    + FENCE + "mermaid\ngraph LR\n" + FENCE + "\n\n"
    + FENCE + "console\n$ pytest\n" + FENCE + "\n\n"
    + block("[src/latest_value.py:1](src/latest_value.py#L1)", "python", "value = compute_latest()")
    + block("[my file.py:1](my%20file.py#L1)", "diff", "+s = 1")
    + block("[my file.py:1](<my file.py#L1>)", "python", "s = 1")
    + block("[caf\u00e9.py:1](caf\u00e9.py#L1)", "diff", "+t = 2")
    + block("[latin.py:1](latin.py#L1)", "python", "a = 1")
    + block("[ff.py:3](ff.py#L3)", "diff", "+b = 2")
    + block("[c.c:4-6](c.c#L4-L6)", "diff title=c.c", "+int g() {", "+  return 2;", "+}", fence="````")
    + block("[app.py:2-3](app.py#L2-L3)", "python", "x = 2", "y = x + 1")
    + "1. A list item:\n\n   [app.py:2](app.py#L2)\n   " + FENCE + "diff\n   +    x = 2\n   " + FENCE + "\n\n"
)


class CheckQuotesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        cls.repo = repo = os.path.join(cls.tmp.name, "repo")
        os.makedirs(repo)
        sh("git", "init", "-q", cwd=repo)
        commit(repo, {
            "app.py": "def f():\n    x = 1\n    return x\n",
            "gone.py": "def old():\n    return 0\n",
            "move_me.py": "a = 1\nb = 2\nc = 3\nd = 4\ne = 5\n",
            "q.sql": "-- keep\n-- drop me\nselect 1;\n",
            "sub/lib.py": "one = 1\n",
            "c.c": "int f() {\n  return 1;\n}\n",
        })
        sh("git", "tag", "base", cwd=repo)
        Path(repo, "latin.py").write_bytes(b"a = 1\nb = '\xe9'\n")
        commit(repo, {
            "app.py": "def f():\n    x = 2\n    y = x + 1\n    return y\n",
            "moved.py": "a = 1\nb = 2\nc = 3\nd = 4\ne = 50\n",
            "q.sql": "-- keep\nselect 1;\n",
            "src/latest_value.py": "value = compute_latest()\n",
            "sub/lib.py": "one = 1\ntwo = 2\n",
            "doc.md": "intro\n" + FENCE + "\ncode\n" + FENCE + "\n",
            "my file.py": "s = 1\n",
            "caf\u00e9.py": "t = 2\n",
            "c.c": "int f() {\n  return 1;\n}\nint g() {\n  return 2;\n}\n",
            "ff.py": "a = 1\n\x0c\nb = 2\n",
        }, delete=["gone.py"], rename=[("move_me.py", "moved.py")])
        sh("git", "tag", "head", cwd=repo)
        Path(cls.tmp.name, "other").mkdir()
        Path(cls.tmp.name, "other", "app.py").write_text("invented()\n")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def copy(self) -> str:
        """A private copy of the repo for tests that change its state."""
        target = tempfile.mkdtemp(dir=self.tmp.name)
        shutil.copytree(self.repo, os.path.join(target, "repo"))
        return os.path.join(target, "repo")

    def check(self, walk: str, *refs: str, repo: str = "", code: int = 0, text: str = "quote failures: 0") -> str:
        path = os.path.join(self.tmp.name, "walk.md")
        Path(path).write_text(walk)
        result = subprocess.run([sys.executable, str(SCRIPT), path, *refs, "--repo", repo or self.repo],
                                capture_output=True, text=True, check=False)
        out = result.stdout + result.stderr
        self.assertEqual(result.returncode, code, out)
        self.assertIn(text, out)
        return out

    def test_good_walkthrough_passes(self) -> None:
        out = self.check(GOOD, *H)
        self.assertIn("production lines shown: 11/13", out)

    def test_refs(self) -> None:
        self.check(GOOD, "nosuchbase", "nosuchhead", code=1, text="failed")
        self.check(GOOD, "base", "HEAD", code=1, text="not HEAD")

    def test_marks(self) -> None:
        cases = [
            ("unchanged line marked +", block("[app.py:1](app.py#L1)", "diff", "+def f():"), "NOT ADDED"),
            ("unchanged } marked + though a } was added", block("[c.c:3](c.c#L3)", "diff", "+}"), "NOT ADDED"),
            ("added line not marked +",
             block("[app.py:1-2](app.py#L1-L2)", "diff", " def f():", "     x = 2"), "NOT MARKED +"),
            ("fabricated removed line",
             block("[app.py:1](app.py#L1)", "diff", " def f():", "-    return 0"), "NOT REMOVED"),
            ("removed line far from its range",
             block("[moved.py:1](moved.py#L1)", "diff", " a = 1", "-e = 5"), "NOT REMOVED"),
        ]
        for name, walk, text in cases:
            with self.subTest(name):
                self.check(walk, *H, code=1, text=text)

    def test_ranges_and_gaps(self) -> None:
        cases = [
            ("huge range", block("[app.py:1-99](app.py#L1-L99)", "python", "def f():"), "LOOSE RANGE"),
            ("out of order",
             block("[app.py:1-4](app.py#L1-L4)", "python", "def f():", "    return y", "    x = 2", "    return y"),
             "out of order"),
            ("added line skipped without ...",
             block("[app.py:1-4](app.py#L1-L4)", "python", "def f():", "    x = 2", "    return y"), "SKIPPED LINES"),
            ("... hiding an added line",
             block("[app.py:1-4](app.py#L1-L4)", "python", "def f():", "    x = 2", "...", "    return y"),
             "TRIMMED CHANGED LINE"),
            ("changed indentation", block("[app.py:1-2](app.py#L1-L2)", "python", "def f():", "x = 2"), "INDENT CHANGED"),
        ]
        for name, walk, text in cases:
            with self.subTest(name):
                self.check(walk, *H, code=1, text=text)

    def test_blocks(self) -> None:
        self.check(block("[app.py:2](app.py#L2)", "diff", "@@ -2 +2 @@", "-    x = 1", "+    x = 2"), *H)
        self.check("- item\n\n  [app.py:2](app.py#L2)\n  " + FENCE + "python\n  invented()\n  " + FENCE + "\n",
                   *H, code=1, text="NOT VERBATIM")
        self.check("Just a story.\n", *H, code=1, text="NO QUOTES")

    def test_paths(self) -> None:
        sub = os.path.join(self.repo, "sub")
        self.check(block("[app.py:1](../other/app.py#L1)", "python", "invented()"), *H, code=1, text="OUTSIDE REPO")
        self.check(block("[lib.py:2](lib.py#L2)", "diff", "+two = 2"), *H, repo=sub)
        self.check(block("[lib.py:2](sub/lib.py#L2)", "diff", "+two = 2"), *H, repo=sub)
        self.check(block("[app.py:2](repo/app.py#L2)", "diff", "-    x = 1", "+    x = 2"), *H)

    def test_hostile_git_config(self) -> None:
        repo = self.copy()
        for key, value in [("diff.noprefix", "true"), ("diff.mnemonicPrefix", "true"), ("color.ui", "always")]:
            sh("git", "config", key, value, cwd=repo)
        self.check(GOOD, *H, repo=repo)

    def test_stale_checkout_warns(self) -> None:
        repo = self.copy()
        commit(repo, {"app.py": "# moved down\ndef f():\n    x = 2\n    y = x + 1\n    return y\n"})
        self.check(block("[app.py:2](app.py#L2)", "diff", "-    x = 1", "+    x = 2"), *H, repo=repo,
                   text="LINK WARNING")

    def test_uncommitted_lines(self) -> None:
        repo = self.copy()
        with open(os.path.join(repo, "app.py"), "a") as file:
            file.write("print(f())\n")
        walk = block("[app.py:5](app.py#L5)", "diff", "+print(f())")
        self.check(walk, *H, repo=repo, code=1, text="NOT VERBATIM")
        self.check(walk, "base", repo=repo)


if __name__ == "__main__":
    unittest.main()
