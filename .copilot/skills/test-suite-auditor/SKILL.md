---
name: test-suite-auditor
description: "Audit or review a test suite for semantic gaps, weak assertions, flakiness, escaped mutations, missing properties, and unsafe input boundaries. Use when asked to audit tests, assess test quality, find missing tests, investigate flaky tests, run mutation/property/fuzz testing, or evaluate whether coverage is meaningful. Supports quick, standard, and deep audits; defaults to audit-only and findings-first reporting."
argument-hint: "[path or target] [quick|standard|deep] [audit-only|repair]"
---

# Test Suite Auditor

Evaluate whether a test suite can detect important regressions. Treat line coverage and
test counts as supporting signals, not proof of quality.

## Operating contract

- Default to **standard, audit-only** when the user does not specify a mode.
- Do not leave persistent production or test changes unless the user explicitly asks for
  repair. Audit-only mode may use the temporary, safely restored experiments described
  below.
- Keep generated reports in chat. Do not create report or planning files unless asked.
- Respect repository instructions, test commands, working-directory rules, and safety
  constraints before running anything.
- Never change host time, network interfaces, firewall rules, shared services, or other
  machine-wide state to create stress. Use dependency injection, test-runner options,
  local proxies, or isolated containers when available.
- Never call a limited sample "flake-free," "fully covered," or "safe." State exactly
  what was inspected and executed.

## Audit depth

Choose the smallest depth that answers the request.

| Depth | Use when | Expected work |
|---|---|---|
| `quick` | A fast review, narrow target, or no execution access | Baseline status, targeted static review, highest-risk gaps |
| `standard` | Default | Baseline, risk map, semantic review, focused execution, one or two applicable advanced techniques |
| `deep` | Explicit comprehensive audit or high-risk release | Repeated flake runs plus broad semantic, mutation, property, and fuzz analysis where each is applicable |

Depth controls breadth, not rigor. A quick audit may inspect fewer paths, but every
reported finding still needs evidence.

## Workflow

### 1. Establish scope and constraints

1. Identify the requested path, target, component, or suite. If none is given, infer a
   bounded scope from the current workspace and say what is included.
2. Read applicable repository instructions and nearby test/build documentation.
3. Inspect and record worktree state before any experiment that could edit files. Assume
  existing changes belong to the user, and preserve the exact pre-experiment contents
  of every file the audit may touch.
4. Identify the canonical test command and the narrowest useful target.
5. Record execution constraints: unavailable dependencies, hardware, credentials,
   network, runtime budget, memory/process limits, or unsafe operations. For a deep
   audit, confirm which mutation, property, and fuzz frameworks or bounded harnesses are
   actually available.

Ask a question only when different plausible scopes would produce materially different
work or risk. Otherwise choose a conservative scope and proceed.

### 2. Establish a baseline

Run the narrowest representative test or existing failing command first. Expand only
when useful and affordable.

Record:

- exact command and working directory
- pass, fail, timeout, or not run
- test count when the runner reports it
- duration when available
- relevant seed, shard, sanitizer, and parallelism settings
- pre-existing failures separately from audit findings

If the baseline fails, isolate the failure. Continue auditing unaffected slices when
possible; do not present later results as a clean-suite audit.

### 3. Build a risk map

Map production behavior to its tests before choosing expensive techniques. Prioritize:

1. safety, security, permissions, money, data loss, and irreversible side effects
2. concurrency, retries, timeouts, clocks, randomness, and shared state
3. parsers, protocol boundaries, serialization, and untrusted input
4. state machines, numerical code, algorithms, and complex boolean guards
5. recently changed or historically fragile behavior

For each selected behavior, locate the controlling implementation, relevant tests, and
the assertion or oracle that would detect a wrong result. Do not spend audit budget on
generated code, trivial accessors, or external-library internals unless boundary logic
makes them risky.

### 4. Review semantic coverage

Semantic review is mandatory at every depth. Check behavior, not merely executed lines.

Look for:

- missing false/default branches and boundary values
- incomplete boolean or state-transition matrices
- success-only coverage of retries, cancellation, cleanup, and partial failure
- assertions that only check "no exception," status codes, mocks, or snapshots without
  validating the important outcome
- tests that reproduce implementation details instead of using an independent oracle
- over-mocking that bypasses integration contracts
- parameterized tests whose cases collapse to the same behavior
- untested error propagation, resource ownership, and side effects
- tests that can pass without executing the intended behavior

Classify a path as **verified**, **gap**, **dead/unreachable**, or **unknown**. Cite the
specific test for verified paths and explain why it is capable of detecting the fault.

### 5. Hunt flakiness when risk justifies it

Use repeated execution for tests involving concurrency, timing, ordering, randomness,
processes, external resources, or prior intermittent failures.

1. Run a control using normal settings.
2. Choose one bounded stressor: repeat count, random order/seed, isolated execution,
   parallelism, sanitizer, fake clock, or injected latency/failure.
3. Record every attempt or runner summary. Preserve seeds and first useful failure.
4. Re-run the failing test alone and under the control settings.
5. Distinguish deterministic failure, order dependence, timing sensitivity,
   environmental failure, and confirmed intermittent failure.

Choose repetitions from runtime and risk; do not blindly run 50 or 100 iterations. Zero
failures in $N$ attempts means only "0 failures observed in $N$ attempts."

### 6. Run mutation testing when assertions are in doubt

Prefer an existing mutation framework. Otherwise use manual mutation only when file
restoration can be proven safe.

Before a manual mutation:

1. Confirm the target file's current worktree status.
2. Save its exact current contents outside the repository or use a reversible patch that
   restores the pre-mutation bytes.
3. Never use `git checkout`, `git restore`, `git reset`, or `git clean` to restore a file
   that may contain user changes.

For each mutation:

1. State the expected behavioral change and the test that should detect it.
2. Apply one compile-valid semantic mutation.
3. Run the narrowest relevant test; broaden only if the narrow test survives and a
   broader suite is affordable.
4. Classify the result as **killed**, **survived**, **not covered**, **equivalent**,
  **timeout**, or **invalid**. A compile error is invalid unless compile rejection is
  the behavior under test.
5. For a survivor, identify an input or observable effect that distinguishes it from the
  original. If no such behavior exists, classify it as equivalent rather than a gap.
6. Restore the exact pre-mutation contents immediately and verify restoration before the
  next mutation.

Count valid, non-equivalent mutations in the score. Uncovered mutants count against the
suite because no test executed the changed behavior:

$$
	ext{kill rate} = \frac{\text{killed}}{\text{killed} + \text{survived} + \text{not covered}} \times 100\%
$$

Do not apply a universal pass threshold. Interpret the score using mutation quality,
sample size, module risk, and equivalent-mutant uncertainty. A surviving mutation is a
finding only when it represents a meaningful observable regression.

### 7. Apply property testing to invariant-rich behavior

Use property testing for pure transformations, numerical code, state machines,
serializers, collections, and algorithms. Prefer the repository's existing framework.

Good properties include round trips, idempotence, conservation, monotonicity, bounds,
metamorphic relations, and agreement with a simple independent oracle. Constrain
generators to valid inputs unless robustness to invalid input is the property being
tested. Record framework settings, seed, case count, minimized counterexample, and
reproduction command.

In audit-only mode, temporary harnesses must not remain in the worktree. Recommend a
permanent regression test for every credible counterexample.

### 8. Apply fuzzing to trust boundaries

Use fuzzing for parsers, decoders, protocol handlers, file formats, public APIs, and
other untrusted-input boundaries. Do not fuzz ordinary internal helpers merely to claim
phase completion.

- Prefer an existing fuzzer and corpus.
- Bound runtime, memory, input size, and process count.
- Use sanitizers where supported and practical.
- Distinguish target crashes from harness failures and resource-limit termination.
- Minimize and preserve the seed or payload needed to reproduce a credible failure.
- Treat expected rejection as success only when it is bounded, documented, and leaves
  state consistent.

### 9. Validate and report

In repair mode, validate each repair with the narrowest test that could falsify it, then
run an appropriate broader check. After mutation or temporary harness work, compare
worktree state and every touched file against the recorded pre-experiment state. Confirm
that user changes are intact and no experiment residue remains.

Report findings first, ordered by severity. Avoid a large inventory of passing tests.

## Evidence and severity

Separate observation from inference:

- **Observed**: produced by a command, failure, counterexample, or directly inspected
  missing assertion.
- **Inferred**: plausible risk that could not be executed or fully traced.
- **Not assessed**: outside scope or blocked.

Use these severities:

| Severity | Meaning |
|---|---|
| Critical | Tests can miss a safety/security failure, destructive behavior, or severe production regression |
| High | Important behavior is unverified or a meaningful mutation/counterexample escapes |
| Medium | Real gap with limited impact or compensating coverage |
| Low | Maintainability, diagnostic quality, or minor edge-case weakness |

Do not assign severity from coverage percentage alone. Include confidence when evidence
is incomplete.

## Output format

Use this compact structure and omit empty sections:

```markdown
## Findings

### [High] Short finding title
- **Location:** `path/to/file.ext:line` and affected test/target
- **Evidence:** observed command/result or exact static evidence
- **Why it matters:** regression the suite can currently miss
- **Recommended test:** concrete setup, action, and assertions
- **Confidence:** high/medium/low

## Audit coverage
| Area | Scope | Technique | Result |
|---|---|---|---|

## Metrics
- Baseline: [status, count, duration]
- Flake runs: [failures/attempts, seeds/settings]
- Mutations: [killed/survived/not-covered/equivalent/invalid; kill rate for valid,
  non-equivalent mutations]
- Properties/fuzzing: [cases, duration, counterexamples/crashes]

## Limits
- [What was not run or inspected and why]

## Recommended order
1. [Highest-value next test or repair]
```

If no findings are found, say so directly, then state the audited scope, commands run,
and residual risk. Never imply that unassessed areas passed.

## Stop conditions

Stop an expensive phase and report when:

- a critical blocker makes results unreliable
- repeated tests threaten rate limits, shared infrastructure, or machine stability
- the mutation target cannot be restored safely
- fuzzing lacks a bounded harness
- enough high-severity gaps are established that more examples would not change the
  recommended next action

Skipped phases are not failures. Name why each was inapplicable, blocked, or outside the
selected depth.
