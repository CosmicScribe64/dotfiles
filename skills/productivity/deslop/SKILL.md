---
name: deslop
description: "Deslop, humanize, de-AI, tighten, or put in plain language any prose: docs, READMEs, code comments, docstrings, commit and PR text, review comments, chat answers. Answer in this style, draft, rewrite, or audit."
argument-hint: "[respond|draft|rewrite|audit] [question, text, path, or base..head]"
---

Make prose clear, short, and human. Clear comes first: cut what the reader doesn't need, and explain plainly whatever they'd otherwise get stuck on. Edit prose only; code, commands, config, and identifiers stay exact.

## Modes

- **respond**: answer in this style, answer first.
- **draft**: write from the facts you have, and ask for any that are missing.
- **rewrite**: edit the given text. In a diff, edit only the lines it adds or changes.
- **audit**: list only findings worth fixing, most important first, as location, problem, fix. For files or diffs, run `scripts/find_tells.py` (`--help` for options); its hits are leads, not verdicts. In procedures, check each step says when it's done and what to do if it fails. "Nothing to fix" is a fine result.

## Cut what the reader doesn't need

Name the reader and their task. Keep a sentence only if it tells them something they can't see from the code or the rest of the text, and they need it. Remove context they already have, how the text or code got here, narration of the implementation, restated declarations, and temporary status. Say each fact once, where the reader will look for it. Delete what fails rather than tightening it. If a doc is organized around internals, reorganize it around what the reader does, and name headings by their task. Keep the existing headings otherwise; don't add new ones.

## Write plainly

- Lead with the point, in active voice.
- One idea per sentence. Use "so," "but," or "because" instead of em dashes or mid-sentence colons.
- Use plain words, without filler ("key," "it's worth noting," "the next step is"), hype, or stacked hedges. Hedge only real uncertainty.
- Prefer plain terms to internal names. Say what happens ("the camera records it"), then give the internal name once if the reader will meet it.
- Call each thing by one exact name, and give the number instead of "significantly."
- Match the shape to the content: a list for separate steps or cases, a table for name-and-meaning pairs, a sentence for one point. Add no headings or lists that repeat each other. In chat, write plain paragraphs, and keep a short reply to one.
- Code comments say only what the code can't: contracts, invariants, bounds, and workaround reasons.
- Review comments say what the code does, the consequence, and the suggested change. An approval is one line.
- Given a voice sample, copy its habits.

## Show the result, not the process

Return the text. When drafts need approval, show them plus one line per decision the user must make. Leave out lists of what you cut or left unchanged, recaps, notes on how you wrote it, next steps, and closing offers.

## Keep every fact

Check the output against the source. Cutting a sentence the reader doesn't need is fine, but every number, unit, date and time anchor ("as of this morning"), condition, warning, identifier, link, and ask that the reader does need must still be there and still true. Invent nothing; mark unknowns as `<placeholder>` or ask.

## Example

Before:

> Great question! I took a look at the deploy logs to see what happened. To give you some background, the staging deploy uses the same Helm chart we talked about yesterday. It turns out the rollout stalled because the `api` pod failed its readiness probe 3 times. Let me know if you'd like me to dig deeper!

After:

> The rollout stalled because the `api` pod failed its readiness probe 3 times.
