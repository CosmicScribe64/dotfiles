# Code cleanup

Use only for explicitly requested executable cleanup. Audits stay read-only. Preserve the
supported contract; cleanup is not feature or architecture work.

## Evidence

Start with the owning implementation and a caller or test. State one redundancy claim
and a focused check that could falsify it. A static type, one caller, or missing tests
cannot prove a runtime boundary redundant: check untyped callers, FFI, serialization,
public consumers, and supported platforms. Keep or escalate when evidence is missing.
For a standalone snippet, only propose a conditional change.

Choose the check for the claim. A compiler or linter covers mechanical changes, not
error, numerical, compatibility, or concurrency equivalence:

| Candidate                         | Check                                                 |
| --------------------------------- | ----------------------------------------------------- |
| Guard, cast, branch, error path   | Accepted and rejected inputs                          |
| Wrapper, shim, or helper          | Tests for every supported consumer and side effect    |
| Duplicate parsing or conversion   | Paired behavior tests on units, defaults, edge cases  |
| Name or alias                     | Build plus reflective or serialized uses              |
| Config or feature flag            | Compatibility across deployed and persisted states    |
| Concurrency or lifecycle          | Lifecycle tests, otherwise human review               |
| Numerical code                    | Boundary or property tests over the supported domain  |

## Protected behavior

Keep validation, authorization, escaping, limits, retries, cancellation, cleanup,
telemetry, and security, privacy, or compliance controls unless proven redundant. Keep
intentional workarounds, suppressions, and actionable TODOs. Public APIs, CLI behavior,
wire formats, and generated output are not local details. Inlining must preserve
evaluation order, lifetime, and exception timing.

## Procedure

1. Run the narrowest meaningful check and require a passing baseline. If none exists, a
   rewrite may first add a test against unchanged code; an audit reports the gap. If the
   check cannot run or fails, leave the code alone and report it.
2. Make one evidenced change, then rerun the same check before anything else.
3. If behavior changed, fix the local defect or withdraw the edit. Never weaken
   assertions, skip cases, or revert pre-existing work to make it pass.
4. Review the diff for changed errors, lost boundaries, and unrelated churn.

Report the evidence, checks run, and remaining limits. A passing build is not runtime
proof.
