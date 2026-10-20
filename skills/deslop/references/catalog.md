# Pattern catalog

Read before an audit, staged review, or file rewrite. Each entry says what to fix and
when to keep the wording. The full pattern list is in
[tells.json](../scripts/tells.json); `find_tells.py --list-rules` prints it.

## Wording

**Announcements and staged emphasis.** Cut "here's the thing," "let's dive in,"
"it's worth noting," "full stop," "let that sink in," "make no mistake," and "real talk"
when they only delay the point. Swapping a formal announcement for a casual one does not
help. Keep "here's the address" when it answers a question, and keep real warnings,
admissions, and "this matters because" when a consequence follows.

**Filler.**

| Wording                      | Revision                         |
| ---------------------------- | -------------------------------- |
| In order to                  | To                               |
| Due to the fact that         | Because                          |
| In the event that            | If                               |
| Has the ability to           | Can                              |
| Conduct an evaluation        | Evaluate                         |
| When it comes to             | Name the subject                 |
| Moving forward               | Name the next action, if given   |
| It is important to note that | Delete                           |
| Utilize, leverage            | Use                              |
| Facilitate                   | Help, or the actual action       |
| Serves as, stands as         | Is                               |
| Boasts, features             | Has                              |

**AI and promotional vocabulary.** Replace "additionally," "crucial," "delve,"
"enhance," "fostering," "garner," "intricate," "landscape," "pivotal," "showcase,"
"tapestry," "testament," "underscore," and "vibrant" with the action or property meant.
One occurrence is enough. Do not trade one vague synonym for another. Technical senses
survive: financial leverage, robust regression, a named framework.

**Metaphor nouns.** "Substrate," "wedge," "vector," "locus," "nexus," "bedrock,"
"paradigm," "north star," "flywheel," and figurative "primitive," "surface,"
"harness," or "scaffolding" usually stand in for a plain word ("base," "way," "goal").
Keep them when they name the real thing: a language primitive, a test harness, an
attack vector.

**Hinge colons.** "If you're coming from cron: you describe conditions" joins two
thoughts. Rewrite as a plain statement. Keep colons before lists, examples, quotations,
labels, and times.

**Hidden actors.** Rewrite passive voice with its actor when known and relevant ("the
compiler validates queries"). Keep passive when the actor is unknown or irrelevant; do
not invent "we" or "you."

**Qualifiers.** Compress stacked hedges ("could potentially affect" becomes "may
affect," not "affects"). Replace "significantly improves" with the measured change, or
flag that none is given. "Only," "approximately," "atomically," "not yet," "at least,"
and "just" can define behavior; keep them when they do. "No evidence of harm" is not
"evidence of no harm."

**Chatbot residue.** Remove "Certainly!," "great question," "you're absolutely right,"
"I hope this helps," "found it!," and follow-up offers from deliverables. Keep them in
quoted transcripts and real correspondence.

## Structure

**Reveals and negative lists.** "Not X but Y" and "not X, not Y, just Z" manufacture a
reveal; state the positive claim when the exclusions add nothing. "Not thread-safe" is
a contract.

**Fragments, punchlines, and forced triples.** Connect "The result?" setups and fragment
stacks. Joining them must not invent causation. If a list has three items, check the
third is real. Keep genuine questions and deliberate narrative emphasis.

**Repetition.** Combine monotonous openings without losing commitments. Do not cycle
synonyms to avoid repetition; a researcher and a principal investigator may differ.

**Tacked-on analysis.** "Highlighting its importance" is empty; a trailing clause about
purpose may assert something real. Read it before deleting.

**Unsupported transitions.** "Because" and "therefore" need support beyond sequence.
Replace a loose "from X to Y" with the actual items; keep real ranges.

**Rejected options.** Remove "a tempting approach would be" setups and empty "I'm not
saying" defenses, but state any failure mode the rejected option revealed.

**Density.** Split sentences the reader must reread. Expand notes ("bad date → exit 2,
no write") into sentences ("The parser rejects a bad date, exits with code 2, and writes
nothing"). Terse notation stays in tables, code, commit subjects, and changelogs.

**Headings and lists.** Remove openings that repeat their heading. Turn enumerating
paragraphs into lists and arguing lists into prose. Keep bold labels that name a field
and add new detail. Do not flatten reference tables into paragraphs.

**Summaries and endings.** Consolidate repeated roadmaps and restated theses. Cut empty
optimistic endings, but keep real plans and limits.

**Metaphors and mannered prose.** Keep analogies that clarify. Cut aphorisms ("wire it or
delete it"), personified code ("the plan holds it"), and figurative verbs ("rides
along") when a literal phrase exists. If a sentence names a feeling ("SQL you can
read"), rewrite it around the mechanism ("`.toSQL()` returns the exact query").

**Comments and docstrings.** Look for banners, paraphrases of the next line, step
narration, duplicated contracts, review-defense rhetoric, and status updates. Public
docs state caller obligations, not private machinery. Keep knowledge that prevents a
known failure, required declaration docs, and directives. Length alone is not
redundancy.

## Claims

**Inflated significance.** Claims of importance, universal benefit, or beauty need a
basis. Separate opinion from established results. "Statistically significant" is not
promotional "significant."

**Borrowed authority.** Ask how a name, award, or analogy supports the point. "Experts
argue" needs a source, not an invented name.

**Speculation.** Remove irrelevant model disclaimers, not meaningful "as of" dates. Keep
unknowns unknown: "the biography omits her early life" is narrower than "her early life
is not documented." Flag speculation; do not stall the whole rewrite.

**Invented concepts.** "The deeper issue" and labels like "the acceleration trap"
announce analysis without supplying it. Describe the supported relationship instead.

## Formatting

| Feature          | Decision                                                                                     |
| ---------------- | -------------------------------------------------------------------------------------------- |
| Em dashes        | Period or comma in prose. Keep ranges, minus signs, and command flags.                       |
| Bold and labels  | Remove competing emphasis and restating labels; keep labels for fields or warnings.          |
| Headings         | Sentence case unless a house style says otherwise; keep proper nouns and stable anchors.     |
| Emojis or arrows | Remove from headings, bullets, and prose; keep meaningful notation in diagrams or tables.    |
| Curly quotes     | Straighten unless the language, format, or protected text requires them.                     |

## Sources

The default rules paraphrase the `unslop` skill in
[cursor/plugins](https://github.com/cursor/plugins/tree/main/pstack/skills/unslop).
Patterns also draw on [tropes.fyi](https://tropes.fyi) by [ossama.is](https://ossama.is),
Wikipedia's [Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing),
the non-fiction entries of the Apache-2.0
[antislop-sampler](https://github.com/sam-paech/antislop-sampler) list, and Kobak et al.
(2025). This catalog is editorial guidance, not an authorship detector.
