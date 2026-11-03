---
name: check-overengineering
description: "Keep a change to the smallest complete diff, or check a plan or diff for overengineering. Use when writing code, planning a change, or asked whether something is overbuilt, too big, or gold-plated."
---

# Check overengineering

Solve the whole problem with the least new code. Inspired by [ponytail](https://github.com/DietrichGebert/ponytail).

## Scope first

Read the task and the code and tests it touches. List every place the change must reach (callers, tests, fixtures, config, exports) and what it could break for users (lost or exposed data, broken callers). That list is the scope.

## The ladder

For each piece of the change, take the first rung that fully works:

1. Not needed, because nobody asked for it. Name it in one line and skip it. A vague request gets the smallest version that does the core job.
2. Already in the codebase: a helper, component, service, or pattern. Use it the way nearby code does.
3. Standard library or platform feature, unless the project has its own.
4. An installed dependency. A few lines never justify a new one.
5. One line a reader understands at a glance.
6. The minimum code that works.

## Rules

- Finish every part the scope list names. The shortest diff wins only once it reaches everything; a one-liner that needs decoding isn't short.
- Keep values in the form the platform gives them, and keep the codebase's layers, interfaces, and conventions.
- Prefer deleting to adding. Add no abstraction, wrapper, option, config, or "for later" code nobody asked for.
- For a bug fix, grep every caller first, then fix the root cause once in the shared code.
- Moved or merged code keeps its error handling and validation.
- Between options of equal size, pick the one correct on edge cases.
- New non-trivial logic (a branch, loop, parser, money or security code, or a new script) gets one small test or assert. Trivial changes need none.
- Mark a shortcut with a known limit as `shortcut: <the limit>, <when to upgrade>`.
- Always keep validation at trust boundaries, error handling that prevents data loss, security, accessibility, hardware calibration, and everything the user asked for.

## Checking a plan or diff

Walk each added piece down the ladder and flag any that sit on a higher-numbered rung than they need, or fall outside the scope list. Also flag scope-list items the change misses. For each finding give the location, the lower rung or missing piece, and the smaller fix. Say so if nothing is overbuilt.

End every reply with one or two lines on what you skipped or did not check, and any risk the user must know.
