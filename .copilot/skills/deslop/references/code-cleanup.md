# Code cleanup

Use for explicit executable-code cleanup. Audits remain read-only. Preserve the
supported contract; do not turn cleanup into feature or architecture work.

## Establish the contract

Start with the owning declaration/implementation and a nearby caller or test. Identify
one redundancy claim and a focused check that could falsify it. Expand inspection only
for relevant boundaries: public consumers, untyped calls, FFI, serialization, generated
bindings, configuration, or supported platforms. Inspect API docs and build/test rules
where they determine the contract.

A static type, one caller, or absent tests cannot establish that a runtime boundary
is redundant. Account for invalid inputs, side effects, defaults, and errors. A one-use
helper may still isolate a contract or support testing. Keep or escalate a candidate
when required evidence is unavailable; do not assume unknown consumers away.

For a standalone snippet, audit or propose a conditional change only. Repository
evidence and a meaningful focused check are required before applying executable
cleanup or claiming verified behavior preservation.

## Candidate evidence

| Candidate                                      | Evidence to inspect                                                                      | Focused check                                                  |
| ---------------------------------------------- | ---------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| Guard, cast, branch, or error path             | Supported inputs, callers, runtime boundaries, invalid-input and error behavior          | Accepted/rejected inputs and applicable typecheck/build        |
| Wrapper, adapter, or compatibility shim        | Public consumers, support policy, side effects, version/platform matrix                  | API/integration tests for supported consumers                  |
| Helper or abstraction                          | All callers, mutation, errors/fallbacks, reuse or testing purpose                        | Success, failure, and side-effect tests                        |
| Duplicate parsing, conversion, or control flow | Authoritative implementation; identical units, defaults, errors, and edge cases          | Paired behavior tests before consolidation                     |
| Name, alias, or local style                    | References, reflection, string lookups, serialized names, generated bindings             | Typecheck/build and reflective/serialized-use tests            |
| Configuration or feature flag                  | Deployed/persisted values, defaults, rollout/support policy, generated config            | Migration/compatibility tests across supported states          |
| Concurrency or lifecycle                       | Ownership, ordering, cancellation, cleanup, races/deadlocks                              | Meaningful lifecycle/concurrency tests; otherwise human review |
| Numerical check or conversion                  | Domain, units, bounds, overflow/underflow, NaN/infinity, rounding, tolerances, precision | Boundary/property tests over the supported domain              |

A compiler or linter may suffice for a mechanical change, not for runtime error,
numerical, compatibility, or concurrency equivalence. Choose checks for the claim,
not merely commands that pass.

## Protected behavior

Retain validation, authorization, escaping, resource limits, retries/backoff,
cancellation, cleanup, telemetry, and observability unless directly proven redundant.
Preserve security, privacy, safety, accessibility, legal, and compliance controls.
Do not remove intentional workarounds, suppressions, directives, or actionable TODOs
merely because they look defensive.

Public APIs, CLI/environment behavior, wire/database formats, and plugin compatibility
are not local implementation details. An authorized API change requires separate
compatibility work. Change generated behavior through its owning source/generator,
not a manual edit to generated output.

Inlining must preserve evaluation count/order, allocation, lifetime, exception timing,
and cleanup. Concurrency changes must preserve locking, atomics, synchronization,
ordering, idempotency, and transactions. Numerical changes must preserve wrapping,
singularities, approximation limits, and the table's domain properties.

## Baseline, change, recheck

1. Select the narrowest meaningful existing check and record its command/environment.
   Inspect side effects first; use isolated fixtures where checks could affect shared
   or user state. Cleanup does not authorize live deployment or data changes.
2. Require a passing baseline before cleanup. If no check exists, an authorized rewrite
   may add a test against unchanged implementation first; an audit only reports the gap.
   If the check cannot run or fails, leave the candidate unchanged and report the blocker.
3. Make one minimal evidenced rename, inline, deletion, or consolidation. Immediately
   rerun the same focused check before further reading or editing.
4. Repair a local defect and recheck, or withdraw only the candidate edit if preservation
   is falsified. Never revert pre-existing work, weaken assertions, skip cases, or narrow
   the supported contract to make cleanup pass.
5. Add necessary regression coverage using repository conventions. Run every new/changed
   test explicitly and the original baseline again after all code/test edits. Additional
   checks are required only by meaningful risk or repository rules.
6. Review the diff for changed errors, lost boundaries, broadened behavior, and unrelated
   churn. Recheck volatile artifacts/configuration when they affect the claim.

Report candidate evidence, preserved behavior, unsupported consumers/states, exact
checks run, and remaining limits. A passing build is not runtime/deployment proof;
claim preservation only within the verified contract.
