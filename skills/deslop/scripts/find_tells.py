#!/usr/bin/env python3
"""List likely AI-writing tells in prose, docs, and code comments.

Every hit is a lead for review under the deslop skill, not a verdict. The script
never edits files. Rules live in tells.json next to this file.

Usage:
  find_tells.py PATH...            scan files or directories (git-tracked files in a repo)
  find_tells.py -                  scan stdin
  find_tells.py --staged           scan lines added in the index
  find_tells.py --diff REF         scan lines added since REF (or in A..B)
  find_tells.py --commits RANGE    scan commit messages in RANGE (for example main..HEAD)
Options: --no-weak, --skip ID[,ID], --json, --list-rules
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROSE_EXTS = {".md", ".markdown", ".mdx", ".txt", ".rst", ".adoc", ""}
HASH_EXTS = {".py", ".sh", ".bash", ".zsh", ".rb", ".pl", ".yaml", ".yml", ".toml", ".conf", ".cfg", ".ini", ".r"}
SLASH_EXTS = {".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx", ".go", ".rs", ".c", ".h", ".cc", ".cpp", ".hpp",
              ".java", ".kt", ".swift", ".cs", ".scala", ".dart", ".php", ".css", ".scss"}
NOTATION_CATEGORIES = {"notation"}  # terse notation is conventional in tables

HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
TABLE_ROW = re.compile(r"^\s*\|")
FENCE = re.compile(r"^\s*(```|~~~)")
BREAK = re.compile(r"^\s*(?:-\s*){3,}$|^\s*(?:\*\s*){3,}$|^\s*(?:_\s*){3,}$")
SENTENCE_END = re.compile(r"(?<=[.!?])[\"')\]]*\s+(?=[A-Z0-9\"'(\[])")
WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")
ORDINAL = re.compile(r"(?:(?:The|A|My|Our) (?:first|second|third|fourth|fifth|sixth|final|last) \w+|(?:First|Second|Third|Fourth|Fifth|Finally|Lastly),)")


# ---------------------------------------------------------------- masking

def blank(text, start, end):
    """Replace text[start:end] with spaces, keeping newlines so offsets and lines hold."""
    return text[:start] + re.sub(r"[^\n]", " ", text[start:end]) + text[end:]


def mask_spans(text, pattern, group=0):
    for m in reversed(list(pattern.finditer(text))):
        text = blank(text, m.start(group), m.end(group))
    return text


def mask_prose(text, ext=".md"):
    """Return (base, full) masks. base hides code, URLs, and markup; full also hides quotations."""
    lines = text.split("\n")
    out, in_fence, in_front = [], False, bool(lines and lines[0].strip() == "---")
    literal_indent = None  # reStructuredText literal block after "::" or a code directive
    for i, line in enumerate(lines):
        if ext == ".rst":
            indent = len(line) - len(line.lstrip())
            if literal_indent is not None:
                if not line.strip() or indent > literal_indent:
                    out.append(" " * len(line))
                    continue
                literal_indent = None
            if line.rstrip().endswith("::") or re.match(r"\s*\.\. ", line):
                literal_indent = indent
                out.append(" " * len(line) if line.lstrip().startswith("..") else line)
                continue
        if in_front:
            out.append(" " * len(line))
            if i > 0 and line.strip() == "---":
                in_front = False
            continue
        if FENCE.match(line):
            in_fence = not in_fence
            out.append(" " * len(line))
        elif in_fence or line.lstrip().startswith(">"):
            out.append(" " * len(line))
        else:
            out.append(line)
    base = "\n".join(out)
    for pat in (r"``[^\n]*?``|`[^`\n]+`", r"\]\([^)\n]*\)", r"<[^>\n]+>", r"https?://\S+", r"<!--.*?-->"):
        base = mask_spans(base, re.compile(pat, re.S))
    # Quoted words are mentioned or quoted, both protected; keep the marks themselves.
    full = mask_spans(base, re.compile(r"\"([^\"\n]|\n(?!\s*\n)){1,300}?\"|“[^”]{1,300}?”"))
    return base, full


def mask_code(text, ext):
    """Keep only comment and docstring text; everything else becomes spaces."""
    keep = [False] * len(text)
    if ext in HASH_EXTS:
        line_comment = re.compile(r"(?<![$'\"\w{])#(?![!{])[^\n]*")
    else:
        line_comment = re.compile(r"(?<![:'\"])//[^\n]*")
    spans = [m.span() for m in line_comment.finditer(text)]
    if ext in SLASH_EXTS:
        spans += [m.span() for m in re.finditer(r"/\*.*?\*/", text, re.S)]
    if ext == ".py":
        spans += [m.span() for m in re.finditer(r"(\"\"\"|''').*?\1", text, re.S)]
    for s, e in spans:
        for k in range(s, e):
            keep[k] = True
    masked = "".join(c if keep[i] or c == "\n" else " " for i, c in enumerate(text))
    masked = re.sub(r"(//+|/\*+|\*+/|^\s*\*|#+|\"\"\"|''')", lambda m: " " * len(m.group()), masked, flags=re.M)
    return masked, masked


def flatten(text):
    """Join soft-wrapped lines with spaces (same length) so phrases can span line breaks."""
    lines = text.split("\n")
    chars = list(text)
    pos = 0
    for i, line in enumerate(lines[:-1]):
        pos += len(line)
        nxt = lines[i + 1]
        joinable = (line.strip() and nxt.strip() and not HEADING.match(line) and not HEADING.match(nxt)
                    and not LIST_ITEM.match(nxt) and not TABLE_ROW.match(line) and not TABLE_ROW.match(nxt)
                    and not BREAK.match(nxt))
        if joinable:
            chars[pos] = " "
        pos += 1
    return "".join(chars)


# ---------------------------------------------------------------- scanning

class Scanner:
    def __init__(self, data, include_weak, skip):
        self.checks = {c["id"]: c for c in data["checks"]}
        self.rules = []
        for r in data["rules"]:
            if r["id"] in skip or (r.get("weak") and not include_weak):
                continue
            flags = re.M if r.get("case_sensitive") else re.M | re.I
            self.rules.append((r, re.compile(r["pattern"], flags)))
        self.include_weak, self.skip = include_weak, skip

    def enabled(self, check_id):
        c = self.checks[check_id]
        return check_id not in self.skip and (self.include_weak or not c.get("weak"))

    def scan(self, text, ext):
        if ext in PROSE_EXTS or ext not in HASH_EXTS | SLASH_EXTS:
            base, full = mask_prose(text, ext)
            prose = True
        else:
            base, full = mask_code(text, ext)
            prose = False
        base, full = flatten(base), flatten(full)
        line_starts = [0] + [m.end() for m in re.finditer("\n", text)]
        table_lines = {i + 1 for i, l in enumerate(text.split("\n")) if TABLE_ROW.match(l)}
        hits = []

        def locate(offset):
            lo, hi = 0, len(line_starts) - 1
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if line_starts[mid] <= offset:
                    lo = mid
                else:
                    hi = mid - 1
            return lo + 1, offset - line_starts[lo] + 1

        def hit(rule_id, start, end, hint, weak):
            line, col = locate(start)
            end_line, _ = locate(max(start, end - 1))
            hits.append({"line": line, "end_line": end_line, "col": col, "rule": rule_id, "weak": bool(weak),
                         "match": " ".join(text[start:end].split())[:80], "hint": hint})

        for rule, pat in self.rules:
            if rule.get("scope") == ("prose" if not prose else "comments"):
                continue
            source = base if rule["id"] == "curly-quote" else full
            for m in pat.finditer(source):
                if m.end() == m.start():
                    continue
                if rule["category"] in NOTATION_CATEGORIES and locate(m.start())[0] in table_lines:
                    continue
                hit(rule["id"], m.start(), m.end(), rule["hint"], rule.get("weak"))

        if prose and ext not in (".rst", ".adoc"):
            self.structure(text, hit)
        self.sentences(full, hit, prose)
        return hits, len(WORD.findall(full))

    def structure(self, text, hit):
        c = self.checks
        lines = text.split("\n")
        offsets, pos = [], 0
        for line in lines:
            offsets.append(pos)
            pos += len(line) + 1
        front_end = -1
        if lines and lines[0].strip() == "---":
            front_end = next((k for k in range(1, len(lines)) if lines[k].strip() == "---"), -1)
        in_fence, prev_level, bold_run, breaks = False, 0, [], []
        heading_lines = []
        for i, line in enumerate(lines):
            if i <= front_end:
                continue
            if FENCE.match(line):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            off = offsets[i]
            h = HEADING.match(line)
            if h:
                level, title = len(h.group(1)), h.group(2)
                heading_lines.append((i, level))
                words = [w for w in WORD.findall(re.sub(r"`[^`]*`", "", title))]
                later = [w for w in words[1:] if len(w) > 3 and not w.isupper()]
                caps = [w for w in later if w[0].isupper()]
                if self.enabled("title-case-heading") and len(caps) >= 2 and len(caps) == len(later):
                    hit("title-case-heading", off, off + len(line), c["title-case-heading"]["hint"], c["title-case-heading"].get("weak"))
                if self.enabled("wh-heading") and re.match(r"(Where|What|Why|How)\s+\w+(\s+\w+){1,}", title) and not title.endswith("?"):
                    hit("wh-heading", off, off + len(line), c["wh-heading"]["hint"], c["wh-heading"].get("weak"))
                if self.enabled("conclusion-heading") and re.fullmatch(
                        r"(?i)(in )?(conclusion|summary|final thoughts|key takeaways|wrapping up|closing thoughts|"
                        r"future (outlook|prospects|directions)|challenges and .*)", title.strip()):
                    hit("conclusion-heading", off, off + len(line), c["conclusion-heading"]["hint"], c["conclusion-heading"].get("weak"))
                if self.enabled("colon-heading") and re.match(r"[^:`]{2,50}: \S", title) and not re.match(r"(?i)(step|part|phase|appendix|example|note|faq)\b", title):
                    hit("colon-heading", off, off + len(line), c["colon-heading"]["hint"], c["colon-heading"].get("weak"))
                if self.enabled("heading-skip") and prev_level and level > prev_level + 1:
                    hit("heading-skip", off, off + len(line), c["heading-skip"]["hint"], c["heading-skip"].get("weak"))
                prev_level = level
            if BREAK.match(line):
                breaks.append(i)
            m = re.match(r"^(\s*(?:[-*+]|\d+[.)])\s+)\*\*([^*\n]+?)\*\*\s*[:.—-]?\s*(.*)$", line)
            if m:
                bold_run.append(i)
                label = WORD.findall(m.group(2).lower())
                after = WORD.findall(m.group(3).lower())[:3]
                if self.enabled("bold-label-restate") and label and after and label[0] in after:
                    hit("bold-label-restate", off, off + len(line), c["bold-label-restate"]["hint"], c["bold-label-restate"].get("weak"))
            elif LIST_ITEM.match(line) or (line.strip() and not line.startswith(" ")):
                if len(bold_run) >= 3 and self.enabled("bold-bullet-run"):
                    s = offsets[bold_run[0]]
                    hit("bold-bullet-run", s, s + len(lines[bold_run[0]]), c["bold-bullet-run"]["hint"], c["bold-bullet-run"].get("weak"))
                bold_run = []
            if self.enabled("bold-density") and not HEADING.match(line) and len(re.findall(r"\*\*[^*\n]+\*\*", line)) >= 3:
                hit("bold-density", off, off + len(line), c["bold-density"]["hint"], c["bold-density"].get("weak"))
        if len(bold_run) >= 3 and self.enabled("bold-bullet-run"):
            s = offsets[bold_run[0]]
            hit("bold-bullet-run", s, s + len(lines[bold_run[0]]), c["bold-bullet-run"]["hint"], c["bold-bullet-run"].get("weak"))
        if self.enabled("section-breaks") and len(breaks) >= 2:
            for b in breaks:
                hit("section-breaks", offsets[b], offsets[b] + len(lines[b]), c["section-breaks"]["hint"], c["section-breaks"].get("weak"))
        for (i, level), (j, nlevel) in zip(heading_lines, heading_lines[1:]):
            if self.enabled("empty-heading") and nlevel > level and all(not lines[k].strip() for k in range(i + 1, j)):
                hit("empty-heading", offsets[i], offsets[i] + len(lines[i]), c["empty-heading"]["hint"], c["empty-heading"].get("weak"))

    def sentences(self, full, hit, prose):
        c = self.checks
        seen = {}
        pos = 0
        for block in full.split("\n"):
            start = pos
            pos += len(block) + 1
            stripped = block.strip()
            if not stripped or HEADING.match(stripped) or TABLE_ROW.match(block):
                continue
            body_start = start + (LIST_ITEM.match(block).end() if LIST_ITEM.match(block) else len(block) - len(block.lstrip()))
            body = full[body_start:start + len(block)]
            sents, last = [], 0
            for m in SENTENCE_END.finditer(body):
                sents.append((last, m.start()))
                last = m.end()
            sents.append((last, len(body.rstrip())))
            sents = [(s, e) for s, e in sents if body[s:e].strip()]
            info = []
            for s, e in sents:
                words = WORD.findall(body[s:e])
                info.append((body_start + s, body_start + e, words))
                if self.enabled("long-sentence") and len(words) > 40:
                    hit("long-sentence", body_start + s, body_start + e, c["long-sentence"]["hint"], c["long-sentence"].get("weak"))
                key = " ".join(w.lower() for w in words)
                if prose and len(words) >= 6 and self.enabled("duplicate-sentence"):
                    if key in seen:
                        hit("duplicate-sentence", body_start + s, body_start + e, c["duplicate-sentence"]["hint"], c["duplicate-sentence"].get("weak"))
                    else:
                        seen[key] = True
            ordinals = [(s, e) for s, e, w in info if w and ORDINAL.match(full[s:e].lstrip())]
            if self.enabled("ordinal-enumeration") and len(ordinals) >= 3:
                check = c["ordinal-enumeration"]
                hit("ordinal-enumeration", ordinals[0][0], ordinals[0][1], check["hint"], check.get("weak"))
            self.runs(info, "fragment-run", lambda w: 0 < len(w) <= 4, hit)
            self.runs(info, "anaphora", lambda w: len(w) >= 3, hit,
                      key=lambda w: " ".join(x.lower() for x in w[:2]))

    def runs(self, info, check_id, qualifies, hit, key=None):
        """Report each maximal run of three or more qualifying sentences once."""
        if not self.enabled(check_id):
            return
        check = self.checks[check_id]
        k = 0
        while k < len(info):
            j = k
            while (j < len(info) and qualifies(info[j][2])
                   and (key is None or key(info[j][2]) == key(info[k][2]))):
                j += 1
            if j - k >= 3:
                hit(check_id, info[k][0], info[j - 1][1], check["hint"], check.get("weak"))
                k = j
            else:
                k += 1


# ---------------------------------------------------------------- inputs

def git(*args, cwd=None):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout


def added_lines(diff_args):
    """Map path -> set of added line numbers from `git diff -U0`."""
    out = git("diff", "-U0", "--no-color", "--diff-filter=AMR", *diff_args)
    result, path = {}, None
    for line in out.splitlines():
        if line.startswith("+++ "):
            path = None if line[4:] == "/dev/null" else line[6:]
        m = re.match(r"@@ -\S+ \+(\d+)(?:,(\d+))? @@", line)
        if m and path:
            start, count = int(m.group(1)), int(m.group(2) or 1)
            result.setdefault(path, set()).update(range(start, start + count))
    return result


def walk(paths):
    for p in paths:
        path = Path(p)
        if path.is_dir():
            try:
                listed = git("ls-files", "-co", "--exclude-standard", "--", ".", cwd=path).splitlines()
                files = [path / f for f in listed]
            except (subprocess.CalledProcessError, FileNotFoundError):
                files = [f for f in path.rglob("*") if f.is_file() and ".git" not in f.parts]
            for f in sorted(files):
                if f.suffix.lower() in PROSE_EXTS | HASH_EXTS | SLASH_EXTS and f.is_file():
                    yield f
        else:
            yield path


def read_text(path):
    try:
        data = Path(path).read_bytes()
    except OSError as e:
        sys.exit(f"find_tells: {e}")
    if b"\0" in data[:4096]:
        return None
    return data.decode("utf-8", errors="replace")


def main():
    ap = argparse.ArgumentParser(description="List likely AI-writing tells. Hits are leads, not verdicts.")
    ap.add_argument("paths", nargs="*", help="files or directories; '-' reads stdin")
    ap.add_argument("--staged", action="store_true", help="scan lines added in the git index")
    ap.add_argument("--diff", metavar="REF", help="scan lines added since REF, or between A..B")
    ap.add_argument("--commits", metavar="RANGE", help="scan commit messages in RANGE, such as main..HEAD")
    ap.add_argument("--no-weak", action="store_true", help="hide noisy rules marked weak")
    ap.add_argument("--skip", default="", help="comma-separated rule ids to skip")
    ap.add_argument("--json", action="store_true", help="print hits as JSON")
    ap.add_argument("--list-rules", action="store_true", help="print rule ids, categories, and hints")
    args = ap.parse_args()

    data = json.loads((HERE / "tells.json").read_text())
    if args.list_rules:
        for r in data["rules"] + data["checks"]:
            print(f"{r['id']:22} {r.get('category', 'structure'):12} {'weak ' if r.get('weak') else '     '}{r['hint']}")
        return 0
    scanner = Scanner(data, not args.no_weak, {s.strip() for s in args.skip.split(",") if s.strip()})

    targets = []  # (display path, text, ext, allowed lines or None)
    if args.commits:
        try:
            log = git("log", "--format=%h%x00%B%x01", args.commits)
        except subprocess.CalledProcessError as e:
            sys.exit(f"find_tells: git failed: {e.stderr.strip()}")
        for entry in log.split("\x01"):
            if "\x00" in entry:
                sha, msg = entry.strip("\n").split("\x00", 1)
                msg = "\n".join(l for l in msg.splitlines() if not re.match(r"(?i)(co-authored-by|signed-off-by):", l))
                targets.append((f"commit {sha}", msg, ".txt", None))
    elif args.staged or args.diff:
        if args.paths:
            sys.exit("find_tells: use paths or --staged/--diff, not both")
        try:
            root = git("rev-parse", "--show-toplevel").strip()
            diff_args = ["--cached"] if args.staged else [args.diff]
            head = None
            if args.diff and ".." in args.diff:
                head = re.split(r"\.\.\.?", args.diff, maxsplit=1)[1] or "HEAD"
            for rel, lines in sorted(added_lines(diff_args).items()):
                ext = Path(rel).suffix.lower()
                if ext not in PROSE_EXTS | HASH_EXTS | SLASH_EXTS:
                    continue
                if args.staged:
                    text = git("show", f":{rel}", cwd=root)
                elif head:
                    text = git("show", f"{head}:{rel}", cwd=root)
                else:
                    text = read_text(Path(root) / rel)
                if text is not None:
                    targets.append((rel, text, ext, lines))
        except subprocess.CalledProcessError as e:
            sys.exit(f"find_tells: git failed: {e.stderr.strip()}")
    elif args.paths == ["-"]:
        targets.append(("<stdin>", sys.stdin.read(), ".md", None))
    elif args.paths:
        for f in walk(args.paths):
            text = read_text(f)
            if text is not None:
                targets.append((str(f), text, f.suffix.lower(), None))
    else:
        ap.print_help()
        return 2

    all_hits, words = [], 0
    for name, text, ext, allowed in targets:
        hits, n = scanner.scan(text, ext)
        words += n
        for h in hits:
            if allowed is None or any(l in allowed for l in range(h["line"], h["end_line"] + 1)):
                h["path"] = name
                all_hits.append(h)
    all_hits.sort(key=lambda h: (h["path"], h["line"], h["col"], h["rule"]))

    if args.json:
        print(json.dumps({"words": words, "files": len(targets), "hits": all_hits}, indent=2))
        return 0
    for h in all_hits:
        weak = " (weak)" if h["weak"] else ""
        print(f"{h['path']}:{h['line']}:{h['col']}: {h['rule']}{weak}: \"{h['match']}\" {h['hint']}")
    counts = {}
    for h in all_hits:
        counts[h["rule"]] = counts.get(h["rule"], 0) + 1
    top = ", ".join(f"{k} {v}" for k, v in sorted(counts.items(), key=lambda kv: -kv[1]))
    strong = sum(1 for h in all_hits if not h["weak"])
    rate = f" {1000 * strong / words:.1f} strong hits per 1,000 words." if words >= 200 else ""
    print(f"\n{len(all_hits)} hits ({strong} strong) in {len(targets)} file(s), {words} words scanned.{rate}"
          + (f" By rule: {top}." if top else ""))
    print("Hits are leads. Judge each one with the deslop skill; a clean run is not a pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
