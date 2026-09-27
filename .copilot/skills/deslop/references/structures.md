# Structure checks

Use for unresolved questions about relationships, organization, rhythm, or comments.
The core supplies the preservation rules; the cases below distinguish useful structure
from empty framing.

## Repeated reversals and negative lists

"Not X but Y" and "not X, not Y, just Z" can manufacture a reveal. State the positive
claim directly only if the exclusions add nothing. "Not thread-safe" is a contract;
"not only input but also output" includes both items. A clipped ending such as "no
guessing" may mean no user guesswork, inferred data, or fallback, so do not choose blindly.

## Questions, fragments, and forced punchlines

Repeated "The result?" setups or fragment stacks may need connection rather than
drama. Keep genuine questions, FAQs, decision prompts, and deliberate narrative
emphasis. Joining two observations must not invent a causal relationship.

## Repeated openings and synonym cycling

Combine monotonous "We will... We will..." openings without losing commitments.
Keep anaphora that builds purposeful emphasis. Do not keep renaming the subject to
avoid repetition: a researcher and a principal investigator are not necessarily the
same person. Repeated labels can improve scanning and consistency.

## Forced groupings

Abstract slogans such as "innovation, inspiration, and insight" add no analysis. When
a list has exactly three items, check whether the third exists to complete the rhythm;
use the natural number. Three actual prerequisites still need all three items.

## Agency, passive voice, and distance

"The decision emerged" may hide responsibility. Default to active voice with the real
actor when it is known: "the loader parses the file," not "the file is parsed by the
loader." An inanimate subject can be accurate, as when a server rejects a request.
Passive voice stays when the actor is unknown or does not matter. Direct address must not
assign the writer's experience to the reader. Ordinary "When" or "What" openings
are not defects by themselves.

## Shallow analysis appended to facts

"Highlighting its importance" may be empty, whereas a trailing clause about purpose,
symbolism, or contribution asserts something distinct. Identify what the tail says
before deleting it. Missing evidence is a claim issue, not a grammar defect.

## False ranges and unsupported transitions

Replace a loose "from X to Y" list with its actual items; retain genuine ranges and
bounds. "Because," "therefore," and "as a result" need support beyond coexistence
or sequence. Chronology does not establish inevitable progress.

## Unraised objections and rejected alternatives

Remove empty "I'm not saying" defenses and "a tempting approach would be" setups.
Keep named objections, real options, corrections, and scope limits. A rejected option
may reveal a failure mode; state that consequence directly instead of discarding it.

## Dense and over-compressed sentences

Split a sentence the reader must reread, or drop its clauses, so each carries one
idea. The opposite failure is prose compressed into notes: dropped articles, verbless
fragments, arrows, and symbols. "Parser rejects bad date → exit 2, no write" becomes
"The parser rejects a bad date, exits with code 2, and writes nothing." Spell out
abbreviations the reader may not know. Terse notation stays in tables, code, commit
subjects, and changelogs where it is the convention.

## Headings, lists, and navigation

Remove an opening that only repeats its heading. Turn "the first... the second..."
paragraphs into a real list when they enumerate, or connected prose when they argue.
Convert inline-header bullets whose bold label and colon restate the line
("**Performance:** Performance improved...") into prose. A lead-in that names the item
and is followed by genuinely new detail ("**Schema in TypeScript.** Tables live in one
file.") is fine. An authorized rewrite may improve ordinary headings and tables under
the core's anchor, data, and numbering protections. Do not flatten scannable reference
information, such as fields or options, into a dense paragraph.

## Repeated summaries and diluted arguments

Consolidate repeated roadmaps, summaries, or renamed versions of one thesis. A standalone
warning or executive summary may serve a different reading path. Keep evidence attached
to its claim. An empty optimistic ending can go; actual plans and limitations cannot
be replaced by generic optimism.

## Metaphors and analogies

Keep analogies that clarify a needed relationship. Cut decoration or a metaphor that
takes more explanation than the concept. Mannered prose goes too: aphorisms ("wire it or
delete it"), rhetorical fragments for effect, personified code ("the plan holds it"),
and figurative verbs ("rides along," "stands on") when a literal phrase exists. Name
what the code or process does. Ask what a sentence tells the reader to do or know; if it
names a feeling ("SQL you can read") rather than a mechanism or number ("`.toSQL()`
returns the exact query string"), rewrite it or cut it. A hypothetical illustration is not evidence;
expanding one does not permit invented facts about a real person or study.

## Comments, docstrings, and implementation history

Inspect contiguous blocks for file banners, symbol/assertion paraphrases, step-by-step
narration, duplicated contracts, review-defense rhetoric, status updates, and brittle
"see above" pointers. Public docs should state caller obligations rather than private
machinery. Length alone does not establish redundancy.

Check required declaration documentation, directives, and traceability citations before
removal. Keep knowledge needed to avoid a known failure. Do not infer a hash map or
complexity bound merely because an old algorithm was slow. Migration guides and release
notes legitimately discuss history; open decisions need an authorized destination.
