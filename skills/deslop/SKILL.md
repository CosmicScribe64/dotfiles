---
name: deslop
description: "Draft, rewrite, or audit prose, documentation, comments, docstrings, messages, and plans, or answer and explain in this style. Use for deslop, humanize, de-AI, tightening, plain language, and document necessity."
argument-hint: "[respond|draft|rewrite|audit] [question, text, path, or base..head]"
---

# Deslop

Make writing useful, direct, and natural in its owner's voice while keeping every necessary meaning and contract. Style patterns are leads, never proof of AI authorship.

## Scope and boundaries

Cover prose, documentation, comments, docstrings, messages, and plans. Never change executable code, even when given a source file or diff. **Respond** when asked to answer or explain in this style (explaining code is a response, not an edit). **Draft** new writing. **Rewrite** when asked to deslop, humanize, tighten, or improve ("review and improve" edits; "review and suggest improvements" audits). **Audit** for reviews, assessments, or when the action is unclear.

Work on the exact text, paths, or refs supplied, and return rewritten pasted text in chat without creating a file. With no target in a repository, compare `HEAD` with its merge base on the remote default branch, or inspect staged and unstaged changes when that diff is empty.

Keep claims, attribution, causation, negation, quantities, units, bounds, ordering, error semantics, obligations, warnings, workaround reasons, actionable TODOs, and qualifiers ("may," "up to," "at least," "only," "not yet"). Do not invent details, citations, actors, experiences, or research. Tightening keeps every distinct claim; an explicit length target permits dropping peripheral details if you note substantive omissions. Unless asked, leave quotations, mandated wording, licenses, generated notices, identifiers, commands, output, code, doctests, directives, link targets, and stable anchors unchanged. When summarizing sources, paraphrase in your own words and quote copied phrases.

Before creating a document, or when reviewing a new one, read it in full and name its reader, the task it supports, and what it adds beyond existing docs and code. A correct document can still be unnecessary when it repeats declarations, narrates implementation, or records temporary status. In authorized cleanup, delete an unnecessary agent-authored document instead of polishing it; in audits or on user-owned writing, report the concern.

## Workflow

1. Establish audience, purpose, medium, and required content. Match a supplied voice sample within the style rules below.
2. Lead with the answer. Put conditions and warnings beside the actions they govern and keep steps in execution order. In a thread reply, state the decision without rebuilding background the other person already knows. Write a revised standalone document for a first-time reader, without "What changed in v2" preambles, "Retracted" or "Misstated" headings, or accounts of how the draft was compiled. Narrative may keep suspense, fragments, and asides.
3. For audits and file or diff rewrites, run `scripts/find_tells.py` on the target (paths, `--staged`, `--diff BASE..HEAD`, or `--commits RANGE`). Every hit is a lead, not a verdict; skip quoted or discussed wording, and a clean run is not a pass. Isolated weak hits, formal or literal grammar, and mixed clinical-and-casual registers in technical, second-language, or neurodivergent writing are not defects on their own.
4. Confirm each suspect span before cutting or flagging it:
   - Cut the span only when no fact, purpose, constraint, invariant, or rationale is lost; when removing a metaphor or framing clause ("serves as the backbone of our disaster-recovery strategy"), keep the underlying purpose ("disaster-recovery").
   - Negate the claim; if no one would assert the negation, replace the platitude with a specific fact or cut it.
   - Ask whether someone who never read the source or code could write the sentence unchanged; if so, replace it with the actual mechanism, metric, or behavior, or cut it.
   - Check whether a named or unnamed authority ("experts argue," "studies show," or a source attached to a trailing "-ing" claim) resolves to a source that supports both the claim and the implied source count. Flag unsupported or unquantified claims and fix harmless wording around them.
   - In code comments and docstrings, remove narration of the next line, step comments, diff history, self-praise ("handles gracefully"), empty qualifiers ("the given request"), non-reasons ("for legacy reasons"), personified code ("the parser wants"), and hardcoded file paths that rot on rename. Keep non-obvious contracts, caller obligations, invariants, numerical bounds, and workaround reasons.
5. Cut framing, compress around the point, and rewrite awkward passages whole instead of swapping words. Compare the result with the original source or brief, not the previous draft, and remove anything an earlier pass added without support.

## Style rules

Apply to every draft, rewrite, and response, and flag violations in audits unless overridden by protected text, an explicit user instruction, or a house style. The full pattern list lives in [tells.json](scripts/tells.json) (`find_tells.py --list-rules`).

**Punctuation and formatting.** No em dashes in prose; end the sentence or use a comma. Keep ranges, minus signs, command flags, and genuine parenthetical asides. Use a colon only before a list, example, quotation, label, or time, not to join two clauses. Use straight quotes unless the format requires curly. Use sentence-case headings, no decorative emojis, and bold only what readers must not miss. Turn bullets whose bold label restates the line into prose; keep bold labels that name a field and add new detail. Do not flatten reference tables into paragraphs.

**Words and actors.** Prefer the plain word ("use," not "utilize" or "leverage"; "is" or "has," not "serves as" or "boasts"; "to," not "in order to"; "because," not "due to the fact that"; "if," not "in the event that"). Replace AI vocabulary, promotional language, stock clichés, and metaphor nouns ("substrate," "wedge," "paradigm," "north star," "flywheel," "dial worth turning," "earns its keep," and figurative "primitive," "surface," "harness," "scaffolding," "load-bearing," or "gated") unless the word is the established technical term. Pick one name for a thing and keep it. Use active voice when a known actor matters. Keep passive when the actor is an automated daemon, a protocol, unknown, or irrelevant, and never invent a person or "we" or "you." Replace an adverb propping up a weak verb with a stronger verb or the number, and replace "significantly improves" with the measured change or flag that none is given. Compress stacked hedges ("could potentially affect" becomes "may affect," not "affects"), and keep isolated human qualifiers ("very," "perhaps," "tends to") when the claim carries content.

**Structure and claims.** One idea per sentence. Write whole sentences in prose; keep terse notation and arrows in tables, code, commit subjects, and changelogs. Cut announcements, staged candor, reasoning leaks, chatbot residue, `<mark>` or `<think>` tags, citation artifacts, and URL tracking parameters. State positive claims directly instead of contrastive reframes ("not just X, but Y," "less like X and more like Y," "is more than a X, it's Y," "rather than merely") unless the exclusion is a contract ("not thread-safe"). Connect fragment stacks and "The result?" setups without inventing causation. Check that the third item in a three-item list adds a distinct idea. Remove unraised objections ("I'm not saying," "a tempting approach would be"), keeping any real failure mode they revealed. Do not stack evidence before asking a question. In commit and PR summaries, state what changed and why; cut canned policy assurances and lists of what was "preserved" or "retained." Cut stock corrective disclaimers ("should be treated as symbolic rather than definitive," "does not by itself establish") unless the domain requires them.

## Output

In **respond** mode, give the answer in this style without an editing narrative. In **draft** or **rewrite** mode, return the finished text; for file edits, check the diff, links, and anchors, and summarize substantive changes, assumptions, and omissions. In **audit** mode, lead with one numbered paragraph per non-overlapping location (lines, problem, consequence, and exact fix, without labeled sub-bullets), note whether a heading edit preserves its anchor, or say if nothing warrants a change. In a **combined** review-and-rewrite, put findings first and the revision second. State findings and summaries in plain language without citing internal rule IDs, check names, or helper scripts.
