# AGENTS.md

## Purpose

This file is the operating contract for autonomous development of the Infrastructure Corridor Optimizer. Keep it concise. Detailed project knowledge belongs in the documents under `docs/`.

## Read First

Before making changes, read:

1. `AGENTS.md`
2. `docs/PROJECT_BRIEF.md`
3. `docs/ARCHITECTURE.md`
4. `docs/PROJECT_STATE.md`
5. `docs/BACKLOG.md`
6. `docs/DECISIONS.md`
7. `docs/QUALITY_GATES.md`
8. Any relevant plan under `docs/plans/active/`

Then inspect the actual repository state. Repository files, code, tests, configuration, generated outputs, git history, and current external-data results are evidence. Documentation may be stale; update it when reality changes.

## Evidence and State Discipline

Always distinguish between:

- **Verified current state** — directly supported by repository evidence or reproduced validation.
- **Planned work** — intended but not yet implemented or verified.
- **Historical decisions** — consequential choices already made and preserved in `docs/DECISIONS.md`.
- **Assumptions** — provisional beliefs that require validation.

Do not claim that code, data, tests, deployment, or functionality exists or works unless evidence supports the claim.

## Normal Autonomous Execution Loop

1. Read the relevant governance documents and inspect the actual repository and Git state.
2. Select the next objective from the prioritized frontier; create an active plan for substantial work.
3. Implement, validate, self-review, and correct the objective according to `docs/QUALITY_GATES.md`.
4. Reconcile `PROJECT_STATE.md`, `BACKLOG.md`, and other documentation with the resulting reality.
5. Complete or archive the plan and commit coherent work when Git access is available and committing is appropriate.

## Normal Authority

Codex is normally authorized to:

- inspect the repository and git history;
- select the next logical work item from the established backlog;
- create execution plans for substantial work;
- implement straightforward technical work;
- make sensible low-risk implementation choices;
- refactor when necessary to complete work cleanly;
- add or update tests;
- run commands, builds, data checks, and validation;
- diagnose and fix failures caused by its changes;
- update project documentation;
- use subagents or parallel work where useful;
- commit coherent completed work when git access is available.

Do not require owner approval for ordinary implementation choices.

## Owner Decision Boundaries

Do not silently make major product, architecture, analytical, data-source, security, cost, visual, or irreversible-data decisions. For this project, owner review is required before treating the study area/endpoints, final routing constraints, hard exclusions versus penalties, route-strategy weight philosophy, or route preset definitions as definitive.

When an owner-level decision is required, stop at that boundary and present:

1. the decision required;
2. relevant evidence;
3. realistic options;
4. a recommendation;
5. consequences of each option.

Exploratory research and benchmarking may continue up to that boundary when it helps make the decision concrete.

## Stop Conditions

Stop when:

- an owner-level decision is required;
- credentials, permissions, unavailable source data, or other external input prevent useful progress;
- continuing would risk destructive or irreversible changes;
- the requested milestone has been completed;
- the remaining work is sufficiently ambiguous that proceeding would likely create substantial rework.

Do **not** stop merely because:

- one task finished;
- a test failed and can be diagnosed;
- an implementation detail was unspecified;
- minor refactoring is needed;
- documentation needs updating;
- a reasonable low-risk technical choice must be made.

## Execution Plans

For significant work, create a short plan under `docs/plans/active/` covering objective, context, approach, acceptance criteria, validation, and risks. Record the outcome and move it to `docs/plans/completed/` when complete. Plans are working artifacts, not architecture records.

## Git Behavior

Unless project-specific evidence requires otherwise:

- inspect `git status` before changing files;
- preserve unrelated user changes;
- never discard or overwrite work merely to obtain a clean tree;
- keep commits coherent and reasonably scoped;
- use descriptive commit messages;
- run relevant validation before committing;
- do not rewrite published history or force-push without explicit permission.

## Documentation Maintenance

Documentation is part of implementation.

- `docs/PROJECT_STATE.md` must describe repository reality after the work finishes.
- `docs/BACKLOG.md` must reflect remaining work rather than completed history.
- `docs/DECISIONS.md` changes only when a consequential decision has actually been made.
- `docs/ARCHITECTURE.md` must distinguish implemented architecture from intended architecture.
- `docs/QUALITY_GATES.md` and this file should change rarely. If repeated agent friction reveals a missing permanent rule, improve the appropriate governance document.

## Self-Review Before Completion

Before declaring a milestone complete, inspect for:

- incomplete implementations;
- accidental scope expansion;
- unsupported assumptions;
- dead or duplicated code;
- missing tests;
- fragile error handling;
- stale documentation;
- misleading claims of completion;
- generated artifacts or temporary files that should not be committed.

The project is a preliminary corridor-screening portfolio application, not a construction-ready engineering system. Preserve that boundary in code, UX, documentation, and claims.
