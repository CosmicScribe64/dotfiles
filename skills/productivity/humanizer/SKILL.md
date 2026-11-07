---
name: humanizer
description: "Rewrite text to remove the signs of AI writing listed on Wikipedia's Signs of AI writing page (puffery, AI vocabulary, negative parallelisms, chatbot framing, canned summaries). Use only when the user asks to humanize text or make it sound less AI-written."
---

# Humanizer

Put the specific fact back. The signs below come from Wikipedia's [Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) and share one root: a model drifts to the most statistically likely phrasing, so a rare, specific fact gets smoothed into a generic, important-sounding claim. "Inventor of the first train-coupling device" becomes "a revolutionary titan of industry": less specific and more exaggerated at once.

The signs are symptoms, not proof. Humans write all of them, and fixing them is not the goal. The goal is prose that says something. Swapping words in a hollow paragraph leaves it hollow, and only makes the hollowness harder to spot: when a sentence has no fact behind it, find the fact or cut the sentence.

## Writing

1. Before drafting, collect the concrete material: names, numbers, dates, paths, commands, what changed, and why. Each sentence carries some of it.
2. Draft in the target register (below).
3. Check the draft against every group under "The signs". Fix each hit by stating the specific claim, or cut it.

## Rewriting a draft

1. Read [signs.md](signs.md) for the full word lists, then scan the draft against every group.
2. For each hit, ask what fact the passage carries. Rewrite it to state that fact; cut it if it carries none. Keep the author's facts, meaning, and register. Add no fact you can't verify: ask, or mark the gap once.
3. Return the rewrite, then a short list of changes grouped by sign, naming any passage cut for having no content and any claim you couldn't check.

Done when every group has been checked, each hit is rewritten to a specific statement or cut, and the rewrite contains no new unverified facts.

## Target register

- **Plain verbs.** is, are, has; used, wrote, moved, tried, died.
- **Definite claims when true.** "the first", "the only", "one of the best", with the evidence.
- **Honest qualifiers.** very, perhaps, tends to, where the uncertainty is real.
- **Varied rhythm.** Sentence length and punctuation (commas, parentheses, colons, a dash) follow the thought. Overcorrecting into uniform short sentences joined only by periods is its own sign.
- Formal, polished, or mixed-register prose is fine. Perfect grammar and an occasional "Additionally" are not signs on their own.

## The signs

As of October 2026 the page names these as the most common signs in new AI text. Check them first:

1. Markdown where it won't render (see "Wrong markup").
2. Canned change summaries (see "Change summaries").
3. Gap disclaimers and corrective framing about sources.
4. Vague association ("associated with", "connected to").
5. Stressing how records or profiles "identify" someone (see "Notability by coverage").

"Older signs" at the end lists what the page now files as historical.

### Content

- **Significance puffery.** "The 2019 move marked a pivotal moment, reflecting broader shifts in the evolving landscape" → "The library moved to Elm Street in 2019." Includes the hedge-then-puff: "While minor, this distinction matters because…".
- **Participle tails.** "…, highlighting its commitment to quality" / "ensuring", "fostering", "contributing to". Cut the tail, or state the consequence and its evidence.
- **Vague association.** "associated with leadership of ExampleCorp" → "was CEO of ExampleCorp in 2017".
- **Weasel attribution.** "Experts argue", "Observers note", "several sources" when there is one, "such as" before a complete list → name who said it, or say it yourself.
- **Notability by coverage.** "featured in leading tech outlets", "active social media presence", "his website identifies him as" → say what the source says, not that it exists.
- **Formula endings.** "Despite its strengths, X faces challenges…" then a hopeful "Future outlook". End where the content ends.

### Language and grammar

- **AI vocabulary in clusters.** delve, tapestry, testament, pivotal, crucial, underscore, showcase, foster, enhance, intricate, vibrant; newer: leverage, multifaceted, quietly, steady, matters. One is coincidence; a cluster is the sign. Read literally: synonyms aren't implicated.
- **Copula avoidance.** "serves as LAAA's exhibition space; the gallery features four rooms" → "is LAAA's exhibition space; it has four rooms".
- **Negative parallelism.** "It's not just a tool, it's a philosophy", "Y rather than X", "no X, no Y, just Z" → state Y. Keep the contrast only when readers really hold X.
- **Rule of three.** "fast, reliable, and scalable" when you have evidence for one → list as many items as exist.

### Style and formatting

- **Headings.** Title Case → sentence case. "X and Y" headings, "Awards and recognition", "Challenges and future directions" are templated shapes. Short replies and comments need no headings.
- **Bold and lists.** Bold scattered through prose; inline-header bullets ("**Speed**: …") for what is really a paragraph → write the paragraph.
- **Emoji** on headings or bullets.
- **Wrong markup for the target.** Markdown where it won't render, prose in a code fence, `---` dividers, curly quotes in code or commit messages.

### Communication meant for the user

- **Chatbot framing in the artifact.** "Certainly!", "Here is a…", "I hope this helps", "Let me know if…", "Would you like…", "You're absolutely right!" → start with the content and end when it ends.
- **Leftover scaffolding.** Placeholders ("[Name]", "2025-XX-XX", "example.com/source1", "(add link here)"), notes to self, "check before publishing" → fill them or ask.
- **Gap disclaimers.** "While specific details are limited…", "not publicly documented", "maintains a low profile", followed by what it "likely" is → state what is known; name an unknown once, without guessing.
- **Corrective framing.** "should be treated as indicative rather than definitive", "does not by itself establish", "it is important to note" → include only a caveat a reader actually needs, stated as a fact.
- **Service-desk register.** "I have carefully reviewed", "apologies for any inconvenience", "please point out any specific issues" → say what you did and what's wrong.

### Citations

- Cite only links, DOIs, ISBNs, page numbers, and quotes you checked resolve and support the sentence. Fabricated or mismatched references are the strongest sign there is.
- Give page numbers for books. Attribute to a source only what the source says; your own analysis stays yours ("Ebert highlighted its lasting influence" needs Ebert to have said it).
- Strip chat artifacts: `utm_source=chatgpt.com`, `contentReference[oaicite:1]`, `↩` back-links.

### Change summaries (commit messages, PR text, changelogs)

- **Canned assurances.** "Improved clarity, flow, and consistency" → "Split install steps by OS; fixed the wrong flag in the example."
- **What you didn't do.** "while preserving existing behaviour", "avoided breaking changes" → mention only what a reviewer would otherwise assume changed.
- **Process over content.** "Added comprehensive tests", "addressed reviewer feedback" → "Test that empty input returns 400", "Rename `cfg` per review".

### Older signs

The page lists these as historical: common in older models, rare in new output. Fix them if they appear, but text without them can still read as AI-written.

- **Promotional tone** (2023–2025). "nestled in the heart of", "boasts", "rich", "groundbreaking", "renowned". Still appears when a user asks for promotional copy.
- **Summary closers.** "In summary", "Overall", "In conclusion" restating the paragraph → stop.
- **Em dashes as punch** (2022–Sept 2026). Spaced "—" to dramatize a clause → a comma, colon, or parentheses. Newer models avoid dashes entirely, and prose held to commas and periods is now the sign (see "Varied rhythm").
- **Elegant variation.** A new synonym for the same thing in each sentence → repeat the noun.
- **Model self-reference.** "As an AI language model", "as of my last knowledge update", refusals → cut.
- **Abrupt cut-offs.** Output that stops mid-sentence → finish or cut the sentence.
