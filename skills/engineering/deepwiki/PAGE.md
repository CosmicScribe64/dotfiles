# Page format

Modeled on Devin's DeepWiki pages. Write for an engineer new to the repo who will open the code next.

## Skeleton

```markdown
# <Title>

**Relevant source files**

- [src/engine/loop.py](<repo>/src/engine/loop.py)
- [src/engine/config.py](<repo>/src/engine/config.py)

<One or two paragraphs: what this page covers and where its scope ends.
Point to neighbours: "For how jobs are queued, see [Scheduler](scheduler.md).">

## <Section>

<Prose, then a diagram or table where one helps.>

Sources: [src/engine/loop.py:40-88](<repo>/src/engine/loop.py#L40-L88), [src/engine/config.py:12](<repo>/src/engine/config.py#L12)
```

`<repo>` is the manifest's `repo` value. Pages sit beside `wiki.json`, so the same prefix works on every page. If the wiki's schema forbids links out of the wiki, cite as `` `path:start-end` `` from the repo root instead (see SKILL.md).

## Rules

- **Citations.** Every section ends with a `Sources:` line. Cite only lines you read in the current file, as `path:start-end` linked to `#Lstart-Lend` (single line: `#L12`). A claim you can't cite gets cut.
- **Scope.** Cover the page's `purpose` and nothing else. Detail that belongs to a child or sibling page gets one sentence and a link.
- **Sections.** Pick the ones the topic needs. Common: purpose and responsibilities, architecture or components, data or control flow, main types and functions, configuration, extension points, errors and edge cases. Overview pages also cover what the repo is for, its top-level layout, and how to build and run it.
- **Diagrams.** Use Mermaid (`flowchart`, `sequenceDiagram`, `classDiagram`, `stateDiagram-v2`) for any flow, call sequence, type hierarchy, or state machine. Label nodes with real identifiers (`Scheduler.enqueue()`, `config.yaml`) so a reader can search for them. Quote labels containing punctuation (`A["parse()"]`). Follow each diagram with a `Sources:` line.
- **Tables.** Use for config keys, CLI flags, message types, and function or class summaries (name, role, file).
- **Code.** Quote a short excerpt only when its exact shape is the point. Otherwise describe it and cite it.
- **Links.** Link other pages by file name (`scheduler.md`). Link the parent and every child at least once.
- **Prose.** Plain and direct.
- **Length.** Write concisely.
