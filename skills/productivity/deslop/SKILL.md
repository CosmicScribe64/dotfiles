---
name: deslop
description: "Draft, rewrite, or audit prose, docs, comments, docstrings, messages, and plans, or answer in this style. Use for deslop, humanize, de-AI, tightening, plain language, and deciding whether a document needs to exist."
argument-hint: "[respond|draft|rewrite|audit] [question, text, path, or base..head]"
---

# Deslop

Make writing clear and concise. Say each thing once, in the fewest plain words that keep its meaning, and sound like a person wrote it. Style patterns are leads, never proof of AI authorship.

## Modes

- **Respond**: answer or explain in this style. Explaining code is a response.
- **Draft**: write something new.
- **Rewrite**: asked to deslop, humanize, tighten, or improve. "Review and improve" edits.
- **Audit**: reviews, "suggest improvements", or when the action is unclear.

Edit prose only; executable code stays as it is. Work on the exact text, paths, or refs given, and return rewritten pasted text in chat. With no target in a repo, use `HEAD` against its merge base on the remote default branch, or the staged and unstaged changes if that diff is empty.

## What goes

Before writing, rewriting, or reviewing a document, a section, or a paragraph of a response, name its reader, the task it serves, and what it adds over existing docs, code, and what the reader already knows. Cut text that repeats declarations, narrates the implementation, explains what the reader already knows, or records temporary status; tightening it is the wrong fix. If it holds a non-obvious reason the code can't show, move that reason into a one-line comment. Delete a whole document only if an agent wrote it and cleanup is authorized; otherwise report it.

## What stays

Of the text that remains, keep claims, attribution, cause, negation, numbers and units, bounds, order, error behavior, obligations, warnings, workaround reasons, actionable TODOs, and real qualifiers ("may," "up to," "only," "not yet"). Leave quotations, mandated wording, licenses, generated notices, identifiers, commands, output, code, directives, link targets, and anchors unchanged unless asked. Add no details, sources, people, mentions, links, or experiences the source lacks. Keeping a meaning never means keeping its wording, so say it in fewer words. Tightening keeps every distinct claim; an explicit length target may drop side details if you name them. Paraphrase sources and quote any copied phrase.

## Workflow

1. Set the audience, medium, purpose, and required content. A supplied voice sample overrides the defaults in "Sound like a person": carry over its humor, asides, sentence rhythm, and stance, not just its plainness.
2. Lead with the answer. Put each condition or warning next to the step it governs, in execution order. In a thread reply, state the decision without rebuilding context the reader already has. A revised document reads fresh: no "what changed in v2", retraction headings, or notes on how it was written.
3. For audits and file or diff rewrites, run `scripts/find_tells.py` on the target (paths, `--staged`, `--diff BASE..HEAD`, or `--commits RANGE`). Hits are leads and a clean run is not a pass. Skip quoted or discussed wording. Formal grammar or mixed registers in technical, second-language, or neurodivergent writing are not defects on their own.
4. Test each suspect span:
   - Cut it only if no fact, purpose, constraint, or reason leaves with it. Dropping a metaphor keeps its point ("the backbone of our disaster-recovery strategy" becomes "disaster recovery").
   - Negate it. If nobody would claim the opposite, replace it with a fact or cut it.
   - Could someone who never saw the source write it unchanged? Replace it with the real mechanism, number, or behavior.
   - Check that each authority ("experts argue," "studies show," a source hung on a trailing "-ing" clause) supports both the claim and the implied number of sources. Flag what it doesn't.
   - In comments and docstrings, cut narration of the next line, step labels, diff history, self-praise ("handles gracefully"), non-reasons ("for legacy reasons"), personified code, and hardcoded paths. Keep contracts, caller obligations, invariants, bounds, and workaround reasons.
5. Rewrite awkward passages whole instead of swapping words. Compare the result with the source, not the last draft, and drop anything an earlier pass added without support.
6. Do a concise pass on the whole text. Try each sentence in fewer words, merge sentences that share a point, and cut any that repeat one, including a closing clause that restates the sentence before it ("so a backport wouldn't reach anyone"). Prefer the short common word and the short sentence. Done when every further cut would lose something from "What stays".

## Style

These apply to every draft and response. Audits flag breaks unless protected text, the user, or a house style overrides them. The full pattern list is [tells.json](scripts/tells.json) (`find_tells.py --list-rules`).

**Sound like a person.** Write like a colleague talking to someone they work with. Keep it short by default, concrete, and willing to say what you think. Explain why only when the reader would otherwise get it wrong. Hedge only where something is uncertain ("I think," "as far as I know"), and keep separate hedges when they cover different unknowns. In chat, write plain paragraphs without headers, bold, or bullets; a document keeps its headings and lists. State a correction directly, with the distinction and what it changes. Fragments and comma splices are fine; leave the prose loose instead of polished, without manufacturing typos or casual filler. Keep cause and effect as separate steps, in order, rather than compressing them into shorthand the reader must decode.

**Punctuation and format.** End the sentence or use a comma where an em dash would go; keep ranges, minus signs, and flags. Use a colon only before a list, example, quotation, label, or time. Use straight quotes, sentence-case headings, no decorative emoji, and bold only for what readers must not miss. Turn bullets whose bold label restates the line into prose. Keep reference tables as tables.

**Words.** Use the plain word ("use," "is," "to," "because," "if"). Replace AI vocabulary, promotional language, clichés, and metaphor nouns ("substrate," "north star," "flywheel," "load-bearing," figurative "surface" or "harness") unless the word is the technical term. Give each thing one name. Use active voice when a known actor matters, and name only real actors, never an invented "we" or "you". Replace an adverb propping up a verb with a stronger verb or the number; "significantly improves" becomes the measured change, or a flag that none is given. Collapse stacked hedges ("could potentially affect" becomes "may affect").

**Structure and claims.** One idea per sentence, in whole sentences; terse notation belongs in tables, code, commit subjects, and changelogs. Cut announcements, staged candor, reasoning leaks, chatbot residue, stray tags, citation artifacts, and tracking parameters. State claims directly instead of "not just X, but Y", unless the exclusion is a contract ("not thread-safe"). Join fragment stacks and "The result?" setups into sentences without inventing causation, and ask a question without stacking evidence first. Make sure a third list item adds a new idea. Give a single sentence or item no heading and no list. Cut objections nobody raised, keeping any real failure mode they revealed. In commit and PR text, say what changed and why, and when explaining why something was left out, name its concrete cost. Cut canned assurances, "preserved" lists, and stock disclaimers.

## Output

- **Respond**: the answer, as short as it can be while complete, with no editing narrative.
- **Draft or rewrite**: the finished text. For file edits, check the diff, links, and anchors, then list substantive changes, assumptions, and omissions.
- **Audit**: only findings worth fixing, most important first, one numbered paragraph each (lines, problem, consequence, exact fix). Group repeats of one problem into one finding. Mention a heading anchor change only if the fix renames a heading something links to. Build suggested replacement text only from facts in the source; mark anything else as a placeholder (`<threshold>`) or a question for the author. Claim only what you checked; with no findings, say so in one line. In a combined review and rewrite, findings come first.

Write findings in plain language, without rule IDs or script names.
