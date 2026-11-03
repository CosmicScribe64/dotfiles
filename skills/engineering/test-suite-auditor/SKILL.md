---
name: test-suite-auditor
description: "Audit or review a test suite for semantic gaps, weak assertions, flakiness, escaped mutations, missing properties, and unsafe input boundaries. Use when asked to audit tests, assess test quality, find missing tests, investigate flaky tests, run mutation/property/fuzz testing, or evaluate whether coverage is meaningful. Supports quick, standard, and deep audits; defaults to audit-only and findings-first reporting."
argument-hint: "[path or target] [quick|standard|deep] [audit-only|repair]"
---

# Test Suite Auditor

Judge whether a test suite would catch important regressions. Line coverage and test
counts are supporting signals, not proof.

## Rules

- Default to **standard, audit-only**. Leave no production or test changes unless the
  user asks for repair; temporary experiments must be restored exactly.
- Report in chat. Create no report or planning files unless asked.
- Follow repository instructions and canonical test commands.
- Never change host time, network, firewall, shared services, or other machine-wide
  state to create stress. Use injection, runner options, or isolated containers.
- Never call a sample "flake-free," "fully covered," or "safe." State exactly what ran.

| Depth      | Use when                                  | Work                                                                     |
| ---------- | ----------------------------------------- | ------------------------------------------------------------------------ |
| `quick`    | Fast review, narrow target, no execution  | Baseline, targeted static review, highest-risk gaps                      |
| `standard` | Default                                   | Baseline, risk map, semantic review, one or two applicable techniques    |
| `deep`     | Explicit comprehensive or high-risk audit | Repeated flake runs plus mutation, property, and fuzz work where useful  |

Depth controls breadth, not rigor: every finding needs evidence.

## Workflow

### 1. Scope

Identify the target; if none is given, choose a bounded scope from the workspace and say
what it covers. Read repository and test docs. Record the worktree state and treat
existing changes as the user's. Find the narrowest test command and note constraints:
dependencies, hardware, credentials, network, time, and memory. For deep audits, check
which mutation, property, and fuzz tools actually exist. Ask only when plausible scopes
differ materially in work or risk.

### 2. Baseline

Run the narrowest representative test first. Record the command, directory, result
(pass, fail, timeout, not run), test count, duration, and any seed, shard, sanitizer,
or parallelism settings. Keep pre-existing failures separate from findings; if the
baseline fails, isolate it and audit unaffected slices without calling them clean.

### 3. Risk map

Map behavior to tests before choosing expensive techniques. Prioritize:

1. safety, security, permissions, money, data loss, irreversible effects
2. concurrency, retries, timeouts, clocks, randomness, shared state
3. parsers, protocols, serialization, untrusted input
4. state machines, numerical code, algorithms, complex boolean guards
5. recently changed or historically fragile code

For each behavior, find the implementation, its tests, and the assertion that would
catch a wrong result. Skip generated code, trivial accessors, and library internals.

### 4. Semantic review (always)

Check behavior, not executed lines. Look for:

- missing false or default branches, boundaries, and state transitions
- success-only coverage of retries, cancellation, cleanup, and partial failure
- assertions that only check "no exception," status codes, mocks, or snapshots
- tests that copy the implementation instead of using an independent oracle
- over-mocking that bypasses real contracts
- parameterized cases that collapse to the same behavior
- untested error propagation, resource ownership, and side effects
- tests that can pass without running the intended code

Classify each path as **verified**, **gap**, **dead**, or **unknown**. For verified
paths, cite the test and say why it would catch the fault.

### 5. Flakiness

Use for tests involving concurrency, timing, ordering, randomness, processes, external
resources, or past intermittent failures. Run a control, then apply one bounded
stressor (repeats, random order or seed, isolation, parallelism, sanitizer, fake clock,
injected latency). Record every attempt and seed. Rerun a failure alone and under
control settings, then classify it: deterministic, order-dependent, timing-sensitive,
environmental, or confirmed intermittent. Pick repetitions from runtime and risk.
Zero failures in $N$ runs means only "0 failures observed in $N$ runs."

### 6. Mutation testing

Use when assertions look weak. Prefer an existing framework. For manual mutation:

1. Check the file's worktree status and save its exact bytes outside the repository.
   **Never** restore with `git checkout`, `git restore`, `git reset`, or `git clean`;
   they wipe uncommitted user changes.
2. Name the expected behavior change and the test that should catch it. Apply one
   compile-valid semantic mutation and run the narrowest test.
3. Classify: **killed**, **survived**, **not covered**, **equivalent**, **timeout**, or
   **invalid** (compile errors, unless compile rejection is the behavior). A survivor is
   a gap only if some input or effect distinguishes it; otherwise it is equivalent.
4. Restore the saved bytes and verify before the next mutation.

$$
\text{kill rate} = \frac{\text{killed}}{\text{killed} + \text{survived} + \text{not covered}} \times 100\%
$$

Apply no universal threshold; interpret the rate by sample size, risk, and equivalent
mutant uncertainty.

### 7. Property testing

Use for pure transformations, numerical code, state machines, serializers, and
algorithms, with the repository's framework. Good properties: round trips, idempotence,
conservation, monotonicity, bounds, metamorphic relations, and agreement with a simple
oracle. Constrain generators to valid inputs unless invalid-input handling is the
property. Record seed, case count, minimized counterexample, and reproduction command.

### 8. Fuzzing

Use for parsers, decoders, protocol handlers, file formats, and other untrusted-input
boundaries, not ordinary helpers. Prefer an existing fuzzer and corpus. Bound runtime,
memory, input size, and processes; use sanitizers where practical. Separate target
crashes from harness failures and resource limits, and keep the input that reproduces a
credible failure.

### 9. Validate

In repair mode, validate each fix with the narrowest test that could falsify it, then a
broader check. After any experiment, compare the worktree and every touched file with
the recorded state, and confirm no temporary harness remains. Recommend a permanent
regression test for every credible counterexample.

## Evidence and severity

Label each finding **Observed** (from a command, failure, counterexample, or inspected
missing assertion), **Inferred** (plausible but not executed or fully traced), or
**Not assessed**.

| Severity | Meaning                                                                   |
| -------- | ------------------------------------------------------------------------- |
| Critical | Tests can miss a safety or security failure, data loss, or severe outage  |
| High     | Important behavior unverified, or a meaningful mutant or counterexample escapes |
| Medium   | Real gap with limited impact or compensating coverage                     |
| Low      | Maintainability, diagnostics, or minor edge cases                         |

Do not derive severity from coverage percentage alone.

## Output

Findings first, by severity. Omit empty sections and do not list passing tests.

```markdown
## Findings

### [High] Short finding title
- **Location:** `path/to/file.ext:line` and affected test
- **Evidence:** command and result, or exact static evidence
- **Why it matters:** the regression the suite can miss
- **Recommended test:** setup, action, and assertions
- **Confidence:** high/medium/low

## Audit coverage
| Area | Scope | Technique | Result |
|---|---|---|---|

## Metrics
- Baseline: status, count, duration
- Flake runs: failures/attempts, seeds
- Mutations: killed/survived/not covered/equivalent/invalid; kill rate
- Properties/fuzzing: cases, duration, counterexamples

## Limits
- What was not run or inspected, and why

## Recommended order
1. Highest-value next test or repair
```

With no findings, say so, then give the scope, commands, and residual risk. Never imply
that unassessed areas passed.

## Stop conditions

Stop an expensive phase and report when results become unreliable, repeated runs
threaten shared infrastructure or machine stability, a mutated file cannot be restored
safely, fuzzing has no bounded harness, or further examples would not change the next
action. Name why each skipped phase was inapplicable, blocked, or outside the depth.
