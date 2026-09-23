# Examples and boundary cases

These synthetic examples illustrate decisions, not actual studies or tested model
behavior. Each source and its stated context supply the available facts.

## 1. Cut filler without changing a bound

Before: "It's worth noting that the import job processes up to 40 files per minute,
and it may slow down on encrypted files."

After: "The import job processes up to 40 files per minute and may slow down on
encrypted files."

Keep "up to," the unit, "may," and the condition. Likewise, "over 3,000 square feet"
must not become "3,000 square feet."

## 2. Improve wording without inventing evidence

Before: "It is worth noting that these findings have important implications for
forecast ensembling and indicate a need for further evaluation."

After: "These findings have important implications for forecast ensembling and
indicate a need for further evaluation."

Remove the filler now; separately flag the unspecified implication. Missing detail
does not require blocking this harmless edit or inventing a mechanism, metric, or study.

## 3. Keep requirements, not their verbosity

Before: "The caller is required to provide the length of the buffer in bytes."

After: "The caller must provide the buffer length in bytes."

Ordinary API documentation may be rephrased while preserving actor, obligation, and
unit. Approved operative wording is different: keep it verbatim and add an explanation
beside it. Three real prerequisites or five commitments still require every item.

## 4. Remove a rejected-option setup, retain the consequence

Before: "Session tokens rotate every 24 hours. A tempting approach would be to restart
the auth service, but restarting ends all active sessions. Rotation happens in place,
and clients refresh transparently."

After: "Session tokens rotate every 24 hours, in place, and clients refresh transparently.
Restarting the auth service ends all active sessions."

The rejected option contains a useful failure mode. Similarly, "not thread-safe" is
a contract, not empty negative rhetoric.

## 5. Select details for an explicit length target

Request: "Cut this batch-failure update to 15 words."

Source: "The batch contained 40 files. Four failed because credentials expired. The
dashboard chart is blue."

After: "Four of 40 files failed because credentials expired."

The failure-focused limit authorizes omitting the peripheral styling fact. Note that
omission outside the rewrite. Keep the denominator and cause. If the request also says
"keep every fact," compress faithfully or explain a genuine conflict.

## 6. Remove narration, retain the convention

In writing mode, this implementation comment may be deleted if no documentation rule
requires it; the code stays unchanged:

```cpp
// Increment retry_count by one.
++retry_count;
```

This coordinate convention supplies information the arithmetic alone may not:

```cpp
// Convert ENU (east, north, up) to NED (north, east, down).
```

## 7. Preserve deliberate narrative choices

Source: "I waited. Nothing. Then the second reply arrived. (I nearly missed it.)"

Keep the suspense, fragments, and aside when they fit the writer's purpose. Do not
force an answer-first sequence, invent a next step, or add the reader's supposed
experience. A narrative can be effective without being a procedure.

## 8. Keep a guard when the runtime contract is unknown

```typescript
export function upperCaseName(name: string): string {
  if (typeof name !== "string") {
    throw new TypeError("name must be a string");
  }
  return name.toUpperCase();
}
```

"Deslop this file" permits writing edits only. Even in explicit code mode, the type
annotation does not constrain untyped consumers. The guard defines rejection and an
error message. Keep it without boundary evidence and a passing focused baseline.
