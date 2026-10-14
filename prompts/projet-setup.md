(Task). Do the setup steps below once. Follow the working rules and baseline rules throughout, including during setup. If CLAUDE.md exists, treat it as AGENTS.md everywhere this file mentions AGENTS.md.

## Setup

1. **Shared repos:** If AGENTS.md is tracked and shared, use an untracked instructions file that loads in every chat (in VS Code, `applyTo: "**"`) in its place, including for the skills' setup. Add every new local file, including the wiki and any copied skills, to `.git/info/exclude`.
2. **Docker:** Build a project Docker image for project code, builds, tests, scripts and their dependencies.
3. **Skills:** If Matt Pocock's skills (https://github.com/mattpocock/skills) aren't installed globally, clone the repo and copy its skills into the project's skills folder; don't use a package manager. Configure them with their setup skill's defaults, using the wiki as the issue tracker and for domain docs.
4. **Wiki:** Create a project wiki following Karpathy's LLM wiki guide (https://gist.githubusercontent.com/karpathy/442a6bf555914893e9891c11519de94f/raw/llm-wiki.md).
5. **Board:** Create a wiki Kanban board in the Obsidian Kanban Plugin format, with one column per status: the configured triage labels (or the triage skill's defaults), plus `blocked`, `in-progress`, `in-review` and `done`. Store each ticket as a wiki page with a `Status:` line. Add a wiki lint that checks wikilinks and fails when a ticket's status doesn't match its column.
6. **Existing work:** If the project already has work in progress, seed the board from the end of any active agent sessions, the project's issue tracker and its open pull requests. Include actions waiting on me.
7. **Coding standards:** Write a CODING_STANDARDS.md suited to the project that links to any existing standards instead of copying them.
8. **Record:** Copy the working rules, baseline rules and the wiki's rules into AGENTS.md, and link CODING_STANDARDS.md from it.

## Working rules

- **Roles:** The agent talking to me is the orchestrator and keeps token use low; no other agent orchestrates. Start every subagent brief with "You are a subagent; do not delegate." Subagents do the work themselves, return a short result, and leave wiki and board updates to the orchestrator unless the brief says otherwise. Use Haiku for read-only subagent tasks and Sonnet for implementation; escalate to Opus only when required.
- **Tools:** Run project code, builds, tests, scripts and their dependencies in the project's Docker image. On the host, use only git, docker, standard shell utilities (such as ls, grep and find) and existing clients for the project's code host and issue tracker (for example gh or curl). Never install packages, libraries or tools on the host (for example with pip, npm or apt). If something can't run in Docker, ask me first.
- **Skills:** Use Matt Pocock's skills (https://github.com/mattpocock/skills) whenever applicable. Take skill names and triage labels from the installed skills and their setup output, not from this file, because upstream updates can rename them.
- **Wiki:** Read the wiki index before starting work, and update the wiki and its log as you learn. In the wiki log, use wikilinks for wiki files and plain paths for everything else. Run the wiki lint after every wiki change.
- **Board:** Track every ticket on the wiki Kanban board, and move its card whenever its status changes. Write each ticket so it can be picked up without the session that created it; a ticket waiting on me gives the exact command to run and where its output goes.
- **Review:** Before a ticket with code changes moves to `done`, use the skills' code review to check the work against CODING_STANDARDS.md and the baseline rules.

## Baseline rules

Solve the whole problem with the least new code. End each reply with one or two lines on what you skipped or didn't check, and any risk I need to know.

Before writing, read the task and the code it touches. List every place the change must reach (callers, tests, fixtures, config, exports) and what it could break for users, such as destroyed or exposed data or broken callers. That is the scope; extra features aren't.

Take the first option that fully works:

1. Skip features, options and flexibility nobody asked for, and name them in one line. A vague request gets the smallest version that does the core job.
2. Reuse what the codebase already has (a helper, component, service or pattern), the way the surrounding code does.
3. Use the standard library or a platform feature, unless the project has its own.
4. Use an installed dependency. Never add a dependency for a few lines.
5. Write one line, if a reader understands it at a glance.
6. Otherwise, write the minimum code that works.

While writing:

- Finish every part the task needs, including the callers, tests and fixtures the change breaks. The shortest working diff wins once you know everything it must touch; a one-liner that needs decoding isn't short.
- Add no abstraction, wrapper, type conversion, option, config, boilerplate or "for later" code nobody asked for. Keep values in the form the platform gives them. Prefer deletion to addition, and keep the codebase's existing layers, interfaces and conventions.
- Comment only the why the code can't show, in one line. Mark a shortcut with a known limit as `shortcut: <the limit>, <when to upgrade>`.
- For a bug fix, find every caller of the function before editing, then fix the root cause once in the shared code.
- Moved or merged code keeps its error handling and validation.
- Between options of equal size, take the one that is correct on edge cases.
- New non-trivial logic (a branch, loop or parser, money or security code, or a new script or app) gets one small test or assert-based self-check. Trivial changes need none.
- Never cut validation at trust boundaries, error handling that prevents data loss, security, accessibility, the calibration real hardware needs, or anything I asked for.
