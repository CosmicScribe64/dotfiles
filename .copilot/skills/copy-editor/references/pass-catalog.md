# Individually runnable editing passes

This is the readable reference for `workshop/passes.json`, the runtime source of
truth. Each entry below is separately runnable with `review-packet --pass ID` or
the browser drawer. Every pass inherits the skill's no-rewrite/no-praise rules,
requires textual evidence and a reader consequence, and permits zero findings.
Exceptions are part of the check, not optional excuses to ignore author voice.

The first 16 labels follow the user-supplied screenshot. The remaining 14 checks
and all prompt details are authored for this package. Each pass is self-contained;
no external reading is required. Catalog order is a navigation aid, not a
requirement to run all checks or edit in that order.

## Writing cleanup

### 0. Sand off filler words

**ID:** `sand-filler-words`

Find qualifiers and padding that do no useful work.

**Focus:** Look only for disposable intensifiers, hedges, redundant qualifiers and padded connective phrases. Locate exact occurrences and explain what information or stance they contribute, if any. Group a repeated habit with representative anchors.

**Exceptions:** Do not ban very, really, actually or unfortunately by word list. Keep emphasis, uncertainty, contrast, comic timing and conversational voice when they do a job. A word count is not a verdict.

**Author task:** Ask the author to test deleting a specified span and decide whether its meaning or tone is needed. Do not supply the shortened sentence.

### 1. Find the real actors

**ID:** `find-real-actors`

Check whether readers can tell who or what acts.

**Focus:** Look for actions whose participants are hidden, unnamed or disguised by abstract nouns. Identify the action and the missing or difficult-to-identify actor. Restrict this pass to identifying actors, not rearranging subjects in otherwise clear sentences.

**Exceptions:** An unknown, irrelevant, collective or deliberately withheld actor need not be named. Never infer an actor that the draft does not establish.

**Author task:** Ask the author to determine and identify the actual participant, or confirm that its omission is intentional.

### 2. Restore actions to verbs

**ID:** `restore-actions-to-verbs`

Find actions buried in nouns.

**Focus:** Look for nominalizations that hide a central action and force extra grammatical scaffolding. Identify the noun phrase carrying the action and the supporting verb that does little work. Explain the specific reading burden.

**Exceptions:** Keep established technical terms, named processes, useful abstractions and nominalizations that connect to prior information. Do not mechanically convert every action noun.

**Author task:** Ask the author to rebuild the clause around its main action, while preserving technical meaning. Do not provide a substitute verb or clause.

### 3. Delete empty verbs

**ID:** `delete-empty-verbs`

Find verb phrases that delay the action.

**Focus:** Look for weak support verbs, unnecessary existence constructions and verbal scaffolding that bury the point without adding time, agency or stance. Keep the diagnosis focused on the empty verbal construction rather than all nominalizations.

**Exceptions:** Be and have are not inherently weak. Existential introductions, careful qualification and tense/aspect distinctions can be necessary.

**Author task:** Ask the author to identify the clause's actual assertion and test removing its empty scaffolding, without supplying a replacement.

### 4. Prefer characters as subjects

**ID:** `prefer-characters-as-subjects`

Check whether subjects help readers follow the participants.

**Focus:** Where the main participants are already identifiable, check whether grammatical subjects align with the people, objects or concepts the passage follows. Flag subjects that force readers to reconstruct the story from abstractions.

**Exceptions:** A character may be an organization, object, process or idea. Do not anthropomorphize concepts or impose human subjects. Topic continuity can justify an abstract subject.

**Author task:** Ask the author to choose a useful subject for the clause in this context. Name the existing participant, but do not draft the sentence.

### 5. Put subjects and verbs together

**ID:** `put-subjects-verbs-together`

Find interruptions between a subject and its verb.

**Focus:** Locate long or nested material between a grammatical subject and its main verb that makes the reader hold an unfinished dependency. Identify both endpoints and the intervening material.

**Exceptions:** Short interruptions, deliberate suspense and necessary qualifications may work. Length alone is not evidence of confusion.

**Author task:** Ask the author to relocate, shorten or separate the intervening material and check that the qualification still applies. Do not show a rewritten clause.

### 6. Put verbs and objects together

**ID:** `put-verbs-objects-together`

Find interruptions between an action and its object.

**Focus:** Locate long interruptions between a verb and its object or required complement. Explain what dependency the reader must retain and which intervening material causes the cost.

**Exceptions:** Do not confuse an optional modifier with a required object. Natural idioms, emphasis and unambiguous short interruptions need not change.

**Author task:** Ask the author to bring the dependent elements together or move the interruption, preserving scope and emphasis.

### 7. Make the opening familiar

**ID:** `make-opening-familiar`

Check the opening of each sentence against prior context.

**Focus:** Read each sentence opening against the preceding passage and the stated audience's knowledge. Identify what the opening asks the reader to recognize, where that information was established, and what new claim the sentence adds. Flag an opening only when the reader must search backward or infer an unstated connection to follow it. Cite the opening and the nearby passage that should supply the connection. Distinguish an unfamiliar term from familiar information described in unfamiliar words. Diagnose sentence-level entry points here, not the whole introduction or the passage's overall topic sequence.

**Exceptions:** Familiar information can come from audience knowledge, not just the preceding sentence. Necessary technical terms need not be replaced. A scene change, surprise, answer to an implicit question, or signaled contrast can start with new information. Do not require repeated openings or mechanically move every new noun later.

**Author task:** Ask the author to decide what the reader already knows and test using that as the entry point, or establish the missing context earlier. Identify existing material that could help; do not supply connecting language.

### 8. Put new and important information last

**ID:** `put-new-important-info-last`

Check what receives a sentence’s final emphasis.

**Focus:** Locate the sentence's main assertion, its contrast or consequence, and the material occupying its ending. Use the paragraph's purpose and surrounding sentences to determine what emphasis readers need; mark uncertainty rather than inventing author intent. Flag a mismatch when routine trailing material receives attention while a needed distinction is buried. Also inspect whether a dense new concept is introduced before the sentence gives readers enough structure to understand it. Cite both the buried information and the ending, and explain the resulting misreading or extra effort rather than merely stating that new information should come last.

**Exceptions:** An ending is one source of emphasis, not a fixed slot for the most important word. Pacing, suspense, parallelism, contrast, and a necessary final qualification can justify the existing order. Preserve the scope of conditions, uncertainty, negation, and exceptions; never move a qualification where it appears to govern a different claim.

**Author task:** Ask the author to choose the intended emphasis and test relocating existing material while preserving the claim and its qualifications. Do not propose an ending or a replacement sentence.

### 9. Repair topic flow

**ID:** `repair-topic-flow`

Follow the sequence of sentence topics.

**Focus:** Map topics at the beginnings of adjacent sentences. Flag abrupt or cycling topic changes that hide the relationship between claims. Diagnose continuity across the passage rather than a single unfamiliar opening.

**Exceptions:** A purposeful change of topic, dialogue or list may not require a continuous chain. Do not erase contrast or replace topic analysis with generic transition advice.

**Author task:** Identify the existing sentence or paragraph whose placement could repair the topic sequence; describe the dependency and possible cost of the move.

### 10. Repair stress flow

**ID:** `repair-stress-flow`

Check whether emphasized endings lead somewhere.

**Focus:** Look at the information stressed at sentence endings and how later sentences pick it up. Flag endings that promise a development that never comes or emphasize details that distract from the argument.

**Exceptions:** A punchline or final image need not be developed in the next sentence. Distinguish a deliberate ending from an abandoned thread.

**Author task:** Ask the author to connect the emphasized information to its next use, reposition it, or decide that the emphasis is not intended.

### 11. Establish a clear topic sentence

**ID:** `establish-clear-topic-sentence`

Check whether a paragraph’s point is discoverable.

**Focus:** For an expository paragraph, distinguish its subject from what it says about that subject. Identify the existing statement that could govern the supporting material, then check whether examples, evidence, and explanation develop that statement. A paragraph can repeat the same topic yet leave its point unclear. Flag a missing, competing, misleading, or needlessly delayed controlling point, citing the opening and the later material that reveals the mismatch. Check whether the paragraph explains how its evidence supports its point rather than expecting quotation or data to explain itself. Identify the connection to the surrounding argument without composing a new claim.

**Exceptions:** Do not require the first sentence to state a thesis. Narrative, dialogue, scene setting, lists, short transitions, and deliberate delayed revelation may have other organizing functions. Evidence and interpretation need not follow one fixed sequence. Do not supply a topic sentence or infer a stronger claim than the text supports.

**Author task:** Ask the author to identify the paragraph's controlling point, decide when readers need it, and align or relocate existing support. If the connection is missing, name the question the author must answer rather than writing the answer.

### 12. Make subjects consistent across a passage

**ID:** `make-subjects-consistent`

Find confusing switches among participants or names.

**Focus:** Track grammatical subjects and the entities they refer to across nearby sentences. Flag needless switches, renamings or inconsistent perspectives that make readers think the participant changed.

**Exceptions:** Real changes of actor and intentional contrast must remain. This is referential continuity, not a demand for identical subjects in every sentence.

**Author task:** Ask the author to decide the passage's viewpoint and keep participant references traceable, or explicitly signal a real switch.

### 13. Control passive voice deliberately

**ID:** `control-passive-voice`

Check whether voice serves emphasis and responsibility.

**Focus:** Identify passive constructions accurately and evaluate their role in topic continuity, emphasis and agency. Flag only those that cause a concrete problem; also note where an attempted active construction disrupts continuity if relevant to a voice decision.

**Exceptions:** Passive voice is not an error. Keep it when the actor is unknown, irrelevant or already established, or when the recipient is the useful topic. Do not count forms of be as passives automatically.

**Author task:** Ask the author to choose grammatical voice based on the reader's topic and need for agency; do not supply the active or passive alternative.

### 14. Name responsibility

**ID:** `name-responsibility`

Find consequential decisions with unclear ownership.

**Focus:** Inspect decisions, obligations, promises, failures, and causal claims whose ownership matters to the reader's next action or interpretation. Check who acts, who is affected, and whether the prose distinguishes an observation from an inference about responsibility. Cite the consequential claim and the wording that obscures its owner or makes uncertain responsibility appear settled. Check nearby context before calling an actor missing. Explain what the reader cannot determine, not just that passive voice or an abstract subject appears. Distinguish factual agency, authority to decide, and moral blame.

**Exceptions:** Do not infer intent, dishonesty, guilt, liability, or an identity absent from the draft. An unknown actor or a protected source may justify omission. Shared or systemic responsibility can be accurate. Do not demand an individual's name where an established team or process answers the reader's question.

**Author task:** Ask the author to establish relevant responsibility from evidence, distinguish known facts from inferences, or explain uncertainty or intentional omission. Preserve source protection and necessary qualifications; do not assign blame or write an accusation.

### 15. Trim metadiscourse

**ID:** `trim-metadiscourse`

Check talk about the writing rather than the subject.

**Focus:** Find announcements of what the author will say, self-commentary, unnecessary reader directions and explanations of the writing process that delay the point. Explain the repeated or missing function.

**Exceptions:** Orientation in complex arguments, uncertainty, humor and purposeful direct address can justify metadiscourse. Do not remove personality by default.

**Author task:** Ask the author to test cutting or shortening the specified commentary and assess what orientation or tone would be lost.

## Structure & argument

### 16. Move misplaced paragraphs

**ID:** `move-misplaced-paragraphs`

Find context or explanations in the wrong place.

**Focus:** Look for existing paragraphs whose relocation would repair a dependency, put evidence next to its claim, or establish context before it is needed. Name source and destination by existing paragraph IDs.

**Exceptions:** Preserve chronology, suspense and prerequisites where intentional. A move can require author-written transitions; do not provide them.

**Author task:** Propose the exact existing paragraph move, explain its benefit, and identify any dependency the author must repair afterward.

### 17. Separate paragraph jobs

**ID:** `separate-paragraph-jobs`

Find paragraphs doing competing kinds of work.

**Focus:** Identify paragraphs that combine claims, evidence, anecdotes or objections in a way that obscures their distinct functions. Explain where the functional turn occurs.

**Exceptions:** A paragraph can legitimately do more than one thing. Do not split solely on word count or enforce uniform paragraph length.

**Author task:** Ask the author to separate, reorder or choose among the competing functions, using existing passage locations rather than new headings.

### 18. Remove duplicate work

**ID:** `remove-duplicate-work`

Find explanations or claims repeated without progress.

**Focus:** Look for sentences or paragraphs that do the same explanatory or argumentative work without adding evidence, precision, perspective or intentional emphasis. Identify both locations.

**Exceptions:** Summaries, reminders after a long gap, refrains and deliberate emphasis may help. Explain what a deletion could lose.

**Author task:** Ask the author to choose which existing treatment to keep, merge in their own words, or preserve for a stated reader need.

### 19. Check logical links

**ID:** `check-logical-links`

Find claims whose stated relationship does not follow.

**Focus:** Check causal, contrastive, comparative and inferential connections. Identify a missing premise, non sequitur, misleading connective or unsupported leap. Separate internal logic from externally verifiable truth.

**Exceptions:** Do not invent evidence or claim to have fact-checked the draft. An explicit hypothesis or personal impression may not need proof but must not be confused with a demonstrated cause.

**Author task:** Ask the author to supply the missing reasoning, narrow the claim, change the asserted relationship or remove the unsupported step.

### 20. Supply missing context

**ID:** `supply-missing-context`

Find concepts introduced before readers can understand them.

**Focus:** For the stated audience, locate terms, references, stakes or prerequisites used before sufficient explanation is available. Identify the exact reader question and where information is needed.

**Exceptions:** Do not explain common domain concepts to an expert audience unnecessarily. Do not generate definitions or factual context for insertion.

**Author task:** Ask the author to supply the needed explanation, move an existing explanation earlier, or establish that the audience already knows it.

### 21. Test the opening’s purpose

**ID:** `test-opening-purpose`

Check whether the introduction prepares this piece.

**Focus:** Identify what readers are being asked to understand, decide, or follow and what the opening gives them to do so. For an argument or proposal, look for the question, difficulty, or gap and the consequence of leaving it unresolved; distinguish a topic's general importance from a reason to read this particular piece. For a narrative, examine the situation, perspective, or tension it establishes instead. Check the opening's promise against what the body actually develops. Flag missing orientation, unsupported stakes, setup the audience already knows, or details readers cannot yet use. Anchor the concern to specific text rather than requesting a more engaging hook.

**Exceptions:** A routine notice or short operational update may need only the event or decision, not a problem-and-solution introduction. Narrative openings and delayed theses can work. Do not invent urgency, reader interests, conflict, novelty, or consequences. Do not prescribe a hook, headline, fixed sequence, or opening formula.

**Author task:** Ask the author to identify the reader's reason for continuing and the minimum orientation it requires. Point to existing setup that could move or be cut; identify unanswered reader questions without writing an opening or supplying stakes.

### 22. Test the ending’s purpose

**ID:** `test-ending-purpose`

Check whether the ending follows from the piece.

**Focus:** Examine whether the ending resolves the stated question, earns its implication, or ends deliberately. Flag unrelated new claims, unearned conclusions or summary that duplicates work without purpose.

**Exceptions:** Open endings, humor, uncertainty and refusal of tidy closure may be intentional. Do not demand a call to action or uplifting takeaway.

**Author task:** Ask the author to decide what the ending should leave with the reader and adjust its scope or position without suggesting closing language.

## Diction & mechanics

### 23. Resolve ambiguous references

**ID:** `resolve-ambiguous-references`

Find pronouns and pointers with competing meanings.

**Focus:** Identify pronouns, demonstratives, comparisons and vague pointers with multiple plausible antecedents or missing referents. Name the competing interpretations with exact evidence.

**Exceptions:** Do not invent intended meaning. Context can resolve a reference that is ambiguous in isolation; do not flag such cases without a reader consequence.

**Author task:** Ask the author to select and make the intended referent explicit, using their own wording.

### 24. Unpack abstractions

**ID:** `unpack-abstractions`

Find abstract claims that readers cannot interpret.

**Focus:** Identify abstractions, compressed noun clusters or labels that conceal a needed mechanism, example or distinction. Explain what the reader cannot tell from the existing text.

**Exceptions:** Established domain language and deliberate generalization are not flaws. Do not replace precise technical vocabulary with generic plain language.

**Author task:** Ask the author to specify the missing mechanism, referent or concrete example, without inventing it for them.

### 25. Catch repeated phrasing

**ID:** `catch-repeated-phrasing`

Find distracting verbal patterns.

**Focus:** Look for conspicuous repeated phrases, stock constructions or nearby repeated words that distract rather than build coherence. Anchor representative occurrences and describe the effect.

**Exceptions:** Keep deliberate rhythm, refrains, terminology consistency and emphasis. Do not offer synonyms or treat raw frequency as proof of a problem.

**Author task:** Ask the author to decide whether the repetition is deliberate and recast or remove selected occurrences themselves.

### 26. Check metaphor and register

**ID:** `check-metaphor-register`

Find imagery or tone that interferes with meaning.

**Focus:** Look for mixed or incompatible metaphors, imagery that contradicts the intended mechanism, unexplained register shifts or references that exclude the intended audience. Describe the precise conflict.

**Exceptions:** Humor, profanity, colloquial language and eccentric imagery may be central to the voice. Do not impose a professional magazine style.

**Author task:** Ask the author to choose the intended image or register and reconcile the conflicting parts, without proposing a new metaphor or phrase.

### 27. Check sentence rhythm

**ID:** `check-sentence-rhythm`

Find sentence patterns that obstruct reading.

**Focus:** Read for pacing and sentence shape, not word count. In a difficult sentence, locate the main clause and the added clauses or phrases; identify where nesting, repeated restarts, or unclear attachment makes the reader lose the main assertion. Distinguish a sequence of details extending a completed clause from interruptions that leave several relationships unfinished. In a list or comparison, check whether mismatched grammatical forms obscure genuinely parallel ideas or whether matching forms falsely suggest equivalence. In adjacent sentences, flag repeated rhythms only when they flatten a meaningful contrast or create a specific reading obstacle. Cite the structural break and its effect, not a preference for musical variety.

**Exceptions:** Long sentences, fragments, repetition, asymmetry, and delayed completion can serve precision, suspense, or voice. Do not impose sentence-length limits, universal short-to-long ordering, or parallelism on unequal ideas. Do not split away a qualification or change which claim a modifier applies to.

**Author task:** Ask the author to locate the main assertion, read the passage aloud, and test moving, grouping, splitting, or combining existing material. State which dependency, contrast, or qualification must survive; do not supply the revised sentence or sequence.

### 28. Diagnose mechanics

**ID:** `diagnose-mechanics`

Check grammar, spelling and punctuation without fixing the copy.

**Focus:** Identify grammatical, spelling and punctuation problems with exact evidence and the relevant convention. Distinguish a probable typo from an intentional variant or quoted material.

**Exceptions:** Respect dialect, house style when supplied, deliberate fragments and unconventional punctuation with a purpose. Do not silently adopt a new style guide.

**Author task:** Name the issue and the convention to check. Do not supply corrected words, punctuation sequences or a corrected sentence, even as a tiny fix.

### 29. Check terminology and consistency

**ID:** `check-terminology-consistency`

Find changes in names, units and presentation conventions.

**Focus:** Check internal consistency of names, abbreviations, technical terms, units, capitalization, numbering and spelling variants. Anchor conflicting occurrences and explain whether they could denote different things.

**Exceptions:** Do not normalize quoted material, domain-specific distinctions or intentional changes. Internal consistency checking is not external fact verification.

**Author task:** Ask the author to choose or clarify the intended term or convention and check the relevant occurrences themselves.

## Broad reviews

### Triage · highest-impact issues

**ID:** `triage`

Find at most five high-impact problems; prioritize dependencies before local polish.

**Focus:** Find at most five high-impact problems; prioritize dependencies before local polish.

**Exceptions:** Retain purposeful voice and distinguish reader problems from taste. This broad review does not count as running any individual checklist pass.

**Author task:** Describe author-controlled revision operations, not replacement prose.

### Structure · broad review

**ID:** `structure`

Examine argument order, paragraph functions, missing premises, late context, and redundant sections. Identify existing paragraph moves by number, not new headings.

**Focus:** Identify the document's apparent question or purpose and the point each section or paragraph contributes. Check both local connections between neighboring passages and the overall progression toward that purpose: repeated terminology and smooth transitions can still hide a missing argument. Compare the opening's promised scope and order with the body. Trace prerequisites, claims, evidence, interpretation, objections, and conclusions where the genre uses them. Locate a missing step, support separated from its claim, competing organizing principles, or sections that repeat a function without advancing the point. For a move, name source and destination by existing locations and test what dependencies it could break. For a gap, state the unanswered reader question rather than inventing its answer.

**Exceptions:** Chronology, suspense, exploratory writing, juxtaposition, and a short practical notice may not need an explicit thesis or roadmap. Do not impose one essay structure, add connective wording to disguise a missing logical link, or rewrite the outline. Preserve purposeful voice and supported uncertainty. This broad review does not count as running any individual checklist pass.

**Author task:** Prioritize the structural problem that would force later rework. Ask the author to clarify the governing point or test specific moves, cuts, or missing reasoning. Identify the existing claims and qualifications that must survive, without supplying new headings, transitions, or arguments.

### Clarity · broad review

**ID:** `clarity`

Examine identifiable actors and actions, buried verbs, ambiguous references, main clauses, and old-to-new information order.

**Focus:** Examine identifiable actors and actions, buried verbs, ambiguous references, main clauses, and old-to-new information order.

**Exceptions:** Retain purposeful voice and distinguish reader problems from taste. This broad review does not count as running any individual checklist pass.

**Author task:** Describe author-controlled revision operations, not replacement prose.

### Economy · broad review

**ID:** `economy`

Examine repetition, throat-clearing, qualifiers, detours and deletion candidates; identify their reader cost and what removing them could lose.

**Focus:** Find wording or passages whose function is already performed elsewhere, whose setup delays a usable point, or whose explanation exceeds this audience's needs. Name the exact removable span and, for redundancy, the other span doing the same work. Inspect padded conditions, repeated negatives, and noun-heavy phrasing for reading cost, but distinguish verbosity from missing thought or evidence that a shorter sentence cannot fix. For each candidate, test whether removing it changes the claim, its force, or the reader's ability to follow it. Separate savings from deletion, relocation, and rewriting; quantify only counted, nonoverlapping deletion spans and never invent a percentage target.

**Exceptions:** Keep meaningful uncertainty, attribution, negation, conditions, exceptions, safety warnings, and technical distinctions. Preserve orientation, deliberate repetition, humor, and pacing when they serve the piece. A useful explanation can add words. Do not offer shorter synonyms, demand maximum compression, or assume a shorter version is better. This broad review does not count as running any individual checklist pass.

**Author task:** Ask the author to test a specific deletion or consolidation and check the meaning and voice at risk. Where a claim is vague rather than redundant, ask what needs clarifying instead of recommending an unsupported cut. Do not produce replacement wording.

### Diction & patterns · broad review

**ID:** `diction`

Examine repeated wording, nominalizations, register shifts, distracting imagery and rhythm. Frequency alone is not a flaw.

**Focus:** Examine repeated wording, nominalizations, register shifts, distracting imagery and rhythm. Frequency alone is not a flaw.

**Exceptions:** Retain purposeful voice and distinguish reader problems from taste. This broad review does not count as running any individual checklist pass.

**Author task:** Describe author-controlled revision operations, not replacement prose.

### Mechanics · broad review

**ID:** `mechanics`

Diagnose grammar, spelling, punctuation and consistency. State conventions but do not supply corrected wording, even a one-word fix.

**Focus:** Diagnose grammar, spelling, punctuation and consistency. State conventions but do not supply corrected wording, even a one-word fix.

**Exceptions:** Retain purposeful voice and distinguish reader problems from taste. This broad review does not count as running any individual checklist pass.

**Author task:** Describe author-controlled revision operations, not replacement prose.

### Full review · broad review

**ID:** `full`

Review structure, then clarity, economy, diction, mechanics. Consolidate related findings. At most 30 findings, fewer whenever justified.

**Focus:** Review structure, then clarity, economy, diction, mechanics. Consolidate related findings. At most 30 findings, fewer whenever justified.

**Exceptions:** Retain purposeful voice and distinguish reader problems from taste. This broad review does not count as running any individual checklist pass.

**Author task:** Describe author-controlled revision operations, not replacement prose.
