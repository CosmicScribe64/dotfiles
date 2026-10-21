# Examples

Synthetic examples of decisions, not tested model behavior.

## 1. Cut filler, keep the bound

Before: "It's worth noting that the import job processes up to 40 files per minute, and
it may slow down on encrypted files."

After: "The import job processes up to 40 files per minute and may slow down on
encrypted files."

"Up to," the unit, "may," and the condition all stay. "Over 3,000 square feet" must not
become "3,000 square feet."

## 2. Fix wording without inventing evidence

Before: "It is worth noting that these findings have important implications for
forecast ensembling and indicate a need for further evaluation."

After: "These findings have important implications for forecast ensembling and
indicate a need for further evaluation."

Separately flag the unspecified implication. Do not invent a mechanism or metric.

## 3. Keep the requirement, not its verbosity

Before: "The caller is required to provide the length of the buffer in bytes."

After: "The caller must provide the buffer length in bytes."

Actor, obligation, and unit survive. Approved operative wording stays verbatim instead.

## 4. Keep the consequence of a rejected option

Before: "Session tokens rotate every 24 hours. A tempting approach would be to restart
the auth service, but restarting ends all active sessions. Rotation happens in place,
and clients refresh transparently."

After: "Session tokens rotate every 24 hours, in place, and clients refresh
transparently. Restarting the auth service ends all active sessions."

## 5. Select details for a length target

Request: "Cut this to 15 words." Source: "The batch contained 40 files. Four failed
because credentials expired. The dashboard chart is blue."

After: "Four of 40 files failed because credentials expired."

Note the dropped chart detail outside the rewrite. If the user also says "keep every
fact," compress faithfully or explain the conflict.

## 6. Cut narration, keep the convention

```cpp
// Increment retry_count by one.
++retry_count;
```

Delete this comment; the code stays. Keep this one, which the arithmetic alone does
not show:

```cpp
// Convert ENU (east, north, up) to NED (north, east, down).
```

## 7. Keep deliberate narrative choices

Source: "I waited. Nothing. Then the second reply arrived. (I nearly missed it.)"

Keep the suspense, fragments, and aside. Do not add a next step. The style rules still
apply: "Nothing — then the second reply arrived" becomes "Nothing. Then the second reply
arrived."

## 8. Replace dashes and hinge colons

Before: "The cache is invalidated on deploy — every node drops its entries. The fix is
simple: warm the cache before traffic shifts."

After: "Each deploy clears the cache on every node. Warm the cache before shifting
traffic."

## 9. Expand compressed notes

Before: "Retry w/ backoff → max 5, then DLQ. No dup writes (idempotency key)."

After: "The worker retries with backoff up to five times, then sends the message to the
dead-letter queue. An idempotency key prevents duplicate writes."

The notation may stay in a table cell or commit subject where it is the convention.
