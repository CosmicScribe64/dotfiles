---
name: change-walkthrough
description: 'Walkthrough of a code change: a short plain spoken story on top, then a breakdown with the changed code quoted beside each idea and linked to file:line, so the reader can understand and review it. Use when the user wants to understand or review a PR, branch, commit range or diff, or asks to explain or walk through code changes.'
---

# Change walkthrough

Tell the change as a story the reader follows top to bottom, with the changed code beside each idea. The reader uses it to review the PR, so they need both the understanding and enough of the actual code to judge it: what each odd-looking piece is for, what changed, and what to check.

## Steps

1. **Scope the diff.** Resolve exactly what to explain: a PR, a branch against its base, a commit range, or the working tree. For a stacked PR, use `base...head` so only that layer's files appear. Read the whole diff, the PR description, commit messages and any linked ticket. Done when you can name every changed file and say which idea it serves.

2. **Find the story.** Write down, for yourself:
   - the problem before the change, in two or three sentences;
   - the stages the data or control flows through, in order;
   - for each stage, the changed code that implements it;
   - every odd-looking piece and the concrete reason it exists (an incident, real data, a review comment, a failing check);
   - for each idea, the one thing a reviewer should verify (an edge case, an ordering assumption, a behaviour change for existing users).

   Done when every changed non-test hunk belongs to an idea, or to the short list of trivial changes (renames, wiring, formatting) you will name at the end.

3. **Resolve quotes in the reader's checkout.** Take each snippet and its line numbers from the files the reader has open (their workspace), not from another worktree or branch, because line numbers differ. Show the whole changed unit (the function, branch or block), up to about 40 lines; trim only unchanged lines, with `...`. For modified code, use a `diff` block with the removed lines (`-`) and added lines (`+`) so the reader sees before and after; for new code, use a plain block in the file's language. Copy code verbatim, whole lines only: `...` stands alone on its own line, and a line too long to quote (minified code) gets a link and a description instead of a block. Done when every quoted new or unchanged line sits inside its cited range, and every removed line exists in the base version.

4. **Write it** to a scratch file, for example `/tmp/walkthrough.md`, in two parts.

   **The story** comes first, under `## The story`: the whole change told as if talking to the reader, in about 400 to 600 words. No code blocks, links, line numbers or file paths; inline code only for a tool or file name the reader will search for.
   - Open with the goal and why it wasn't possible before the change; a short bullet list is fine when there are several reasons.
   - Walk through the parts in the same order as the breakdown, giving each a bold name ("the **generator**"). Say what it does and why it's needed in everyday terms, explaining any idea a later part relies on where it first appears (such as why replay needs a warm-up), with a concrete example from the real data ("point it at a folder and say 'around 22:43, give me 90 seconds after'"). Skip internal mechanics such as encodings and precision.
   - Give at most five odd-looking pieces one short bullet each, picking the ones caused by something that actually happened (real data, an incident, a review), and say what happened. Leave validation, error handling and edge-case guards to the breakdown.
   - Call out bugs found along the way and behaviour changes for existing users plainly, and say who they affect today, checking real data where you can; if you can't check, say so.
   - End with one sentence on what else the change contains (tests, docs), then a line pointing to the breakdown below.

   The reader should understand the whole change from this part alone, before reading any code.

   **The breakdown** follows, under `## Code walkthrough`.
   - One paragraph per idea, in flow order. Start each with a bold lead-in naming the idea ("**Rotation handover.**"), explain what it does and why in plain words, then put the link on its own line, `[file.py:329-347](path/file.py#L329-L347)`, directly above the code block. Follow the code with one sentence starting "**Check:**" that names what to verify.
   - For each idea with a test, quote the one test that best pins its behaviour, after the code.
   - Use real values where you have them (topic names, counts, timestamps, the example that triggered the fix).
   - Close with one sentence naming the trivial changes and remaining tests you left out, and one next action that links the densest spot to read in context.

5. **Check the quotes.** Run `python3 <this skill's folder>/scripts/check_quotes.py /tmp/walkthrough.md <base> <head> --repo <reader's checkout>`. Fix each failure; most are a range a few lines off, so look up the first quoted line's real number in the checkout. When it reports under half of the production lines shown, add the missing changed units or name them in the closing sentence. Done when it reports 0 quote failures and 0 diff warnings; then show the walkthrough to the reader.

## Style

Talk to the reader in flowing prose: plain words, one idea per paragraph. In the breakdown, each idea is followed by its code. Every changed line of production code should be visible in a snippet or named in the closing sentence; the reader should be able to approve or question the PR from this walkthrough alone.
