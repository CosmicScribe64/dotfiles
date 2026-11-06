---
name: deepwiki
description: 'DeepWiki-style code pages in an LLM wiki: plan, generate, update (one page or in bulk), ask, and lint per-repo architecture pages with line-level source citations and diagrams. Use when asked to create a deepwiki or code wiki for a repo, document a codebase as wiki pages, or refresh code wiki pages after the code changed.'
---

# DeepWiki

Recreates Devin's DeepWiki inside an LLM wiki (the `llm-wiki` skill): a tree of topic pages per repo, each grounded in source with line-range citations and Mermaid diagrams, kept fresh by recording the commit each page was written against.

## Layout

The repo is a raw source: read it, never edit it. Each repo gets one folder in the wiki:

```
<wiki>/code/<repo-name>/
  wiki.json    structure and state; the single source of truth
  index.md     numbered page tree, written by the script
  <slug>.md    one page per topic, format in PAGE.md
```

Pages follow topics (subsystems, flows, concepts), not directories. Each page's `sources` maps it to files, so a changed file leads straight to the pages to update.

If the wiki doesn't exist yet, set it up with the `llm-wiki` skill first. When adding a repo, link `code/<repo-name>/index.md` from the wiki's `index.md` and add this rule to its schema: "Pages under `code/` are maintained with the deepwiki skill."

The wiki's schema wins over PAGE.md: follow its front matter, required sections, log format and link rules. If it forbids links out of the wiki, write citations as backticked repo-root paths (`` `src/engine/loop.py:40-88` ``, or `` `./README.md:1-10` `` for a file at the root) instead of links; `check` validates both forms.

## wiki.json

A superset of Devin's `.devin/wiki.json`. If the repo has one, import its `repo_notes` and `pages` as the starting plan (titles become slugs; parent titles become parent slugs).

```json
{
  "name": "nanoGPT",
  "repo": "../../../../nanoGPT",
  "repo_notes": [{ "content": "train.py is the hot path; document it first.", "author": "Lila" }],
  "ignore": ["*.lock", "assets/"],
  "pages": [
    {
      "slug": "overview",
      "title": "Overview",
      "purpose": "What nanoGPT is, its layout, and how training, sampling and data prep connect",
      "parent": null,
      "sources": ["README.md", "train.py", "sample.py"],
      "page_notes": [],
      "commit": null
    }
  ]
}
```

- `repo`: repo root, relative to this file.
- `repo_notes`, `page_notes`: steering from the user. Follow them in every page they apply to.
- `ignore`: files no page needs to explain.
- `pages`: reading order. `parent` is a slug. `sources` entries are file paths, directory paths, or fnmatch globs (`*` crosses `/`).
- `commit`, `dirty`: written by `stamp` only.

## Script

`python3 <this skill's folder>/scripts/deepwiki.py <command> <wiki.json>`:

- `stale`: JSON listing `missing` pages (never written), `stale` pages with the changed files behind each, `empty_sources` pages whose sources match nothing, and `uncovered` files no page or `ignore` entry covers.
- `check`: broken links and cited files, citation line ranges past the end of the file, pages missing from disk or from `wiki.json`, unknown parents. Exit 1 on any problem.
- `stamp <slug>... | --all`: record HEAD as each page's `commit`. If a page's sources have uncommitted edits, it also records their content in `dirty`, so `stale` flags them only once they change again.
- `index`: rewrite `index.md` from `wiki.json`.

## Plan

1. Read the README, build files, entry points, `git ls-files`, and existing docs.
2. Draft the tree: an Overview page first, one top-level page per subsystem, children for parts a reader needs on their own. A mid-size repo lands around 10 to 30 pages with 3 to 15 source files each. Each `purpose` names the directories, files, or concepts it covers.
3. Write `wiki.json` with `commit: null` and run `stale`. Assign every `uncovered` file to a page or to `ignore`. Done when `uncovered` is empty and `check` reports only missing pages.
4. Run `index`, show the user the tree, and apply their changes before generating.

## Generate

One page: read PAGE.md and the page's `wiki.json` entry, read its source files, and write `<slug>.md`.

Bulk: hand pages to subagents in batches of 2 to 5. Give each the absolute paths of `wiki.json`, PAGE.md and the repo, plus its slugs. Subagents read files with file tools, write only their own pages with file-creation tools, and leave `wiki.json` alone.

Then finish: run `check` and fix until it reports 0 problems, `stamp` the written slugs, run `index`, and append a log entry in the wiki's format naming the repo and slugs.

## Update

1. Run `stale`.
2. For each stale page, read `git diff <commit> -- <changed files>` and the current files. Edit the sections the change affects and leave the rest as it is. Recompute every citation into a changed file, including in untouched sections, since shifted lines break them. For one page, do this yourself; for many, batch to subagents as in Generate.
3. Fix the structure:
   - `missing`: generate the page.
   - `empty_sources`: merge the page into a neighbour or delete it, and repoint links to it.
   - `uncovered`: add the file to the right page's `sources` and update that page, add a new page, or add it to `ignore`.
4. Finish as in Generate.

When the user asks for a full regenerate, or the tree no longer fits the code, rerun Plan, keep the slugs that survive, and regenerate every page.

## Ask

Answer from the wiki first: `index.md`, then the relevant pages. Confirm each point in the current source and cite `path:lines`. If a page turns out stale, say so and update it. Offer to file an answer worth keeping as a new page: add it to `wiki.json` with its sources, then Generate it.

## Lint

Run `check` and `stale`, then read the pages for contradictions between them, flows described without a diagram, and pages straying outside their `purpose`. Report findings and fix the ones the user approves.
