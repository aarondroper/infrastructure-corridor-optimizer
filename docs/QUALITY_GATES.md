# Quality Gates

## Purpose

These gates define what an agent must consider before declaring work complete. Apply only the gates relevant to the current change, but do not silently skip applicable validation.

Exact commands should be added or updated once the repository establishes its real tooling. Never invent passing status: record what was actually run and what evidence exists.

## 0. Current Repository Baseline and Applicability

The current repository has a dependency-light Python analytical core, a standard-library
unit test suite, a minimal `pyproject.toml`, and an endpoint acquisition script. It has
no configured linter/type checker, full geographic data pipeline, frontend build, or
deployment. For Python/core changes, run the documented unit tests and relevant
acquisition checks in addition to repository inventory and consistency checks:

- `find . -maxdepth 4 -type f -print | sort` to inventory files;
- `rg --files` to confirm the source/configuration surface;
- `rg -n` searches for stale implementation claims, unsupported completion claims, and broken document references;
- `PYTHONPATH=src python3 -m unittest discover -s tests -v` for the current analytical core;
- `PYTHONPATH=src python3 scripts/acquire_sources.py --output <temporary manifest>` for live endpoint validation when network access is available;
- `PYTHONPATH=src python3 benchmarks/benchmark_routing.py --sizes 128 256 512` for the current routing proxy benchmark;
- direct review of all changed Markdown files;
- `git status --short --branch`, `git diff --check`, and the relevant diff when a usable Git repository exists.

Do not substitute guessed commands such as `pytest`, `npm test`, or a frontend build until the repository contains the corresponding tooling. When a gate is not applicable, record the reason and the evidence establishing that fact. An empty or unusable `.git` directory is not evidence of a clean Git state and must be reported as such.

## 1. Correctness

Before completion:

- the implemented behavior matches the active objective and approved project scope;
- no known placeholder is presented as finished functionality;
- routing logic, assessment outputs, exports, and UI values agree on the same underlying route/configuration;
- failure cases do not silently produce plausible-looking but invalid outputs;
- the diff has been reviewed for accidental scope expansion or unrelated changes.

## 2. Automated Tests

Important logic should receive automated coverage where practical.

Priority test targets include:

- cost normalization/transformation;
- weighted cost combination;
- hard-exclusion handling;
- routing correctness on small controlled grids;
- no-path/disconnected cases;
- route statistics;
- raster/vector and geometric intersections;
- crossing detection/counting;
- export geometry and attributes;
- configuration parsing/validation;
- provenance metadata generation.

Bug fixes should normally include a regression test when the failure can be represented reliably.

## 3. Linting and Static Analysis

Run the repository's configured linting/static-analysis tools for changed code.

Requirements:

- no new lint errors in changed code;
- suppressions must be narrowly justified;
- generated files should not be linted manually if project tooling intentionally excludes them.

The actual toolchain is currently unverified and must be documented once established.

## 4. Type Checking

Where static typing is configured:

- run the relevant Python and/or TypeScript type checks;
- do not introduce broad `Any`, unsafe casts, disabled checks, or ignored errors merely to obtain a clean run;
- externally sourced data should be validated at boundaries rather than assumed correct.

## 5. Build Success

For changes affecting buildable components:

- the Python package/project should install or execute using documented setup;
- the frontend production build should succeed;
- generated asset steps required by the app should complete successfully;
- no missing-file or environment assumptions should be hidden by a developer's local machine.

## 6. Data Validation

For data-ingestion or transformation work, validate at minimum as applicable:

- source access succeeds and expected content is returned;
- licensing/provenance metadata is recorded where required;
- expected study-area coverage exists;
- CRS is known and correct;
- raster resolution/grid alignment is intentional;
- vector geometries are valid or repaired explicitly;
- required attributes exist and have plausible values;
- clipping/subsetting does not unexpectedly remove required features;
- nodata and missing values are handled explicitly;
- output counts, extents, ranges, and summary statistics are plausible;
- stale or partial cached inputs cannot silently masquerade as complete outputs.

## 7. Analytical / Scientific Validity

This project requires methodological self-review, not just code execution.

Before declaring analytical work complete:

- source variables have a documented interpretation;
- transformations into cost values are transparent;
- units and scale are understood;
- hard exclusions are distinguished from penalties;
- weights are presented as assumptions, not objective facts;
- normalization avoids unjustified precision;
- routes visibly respect exclusions and respond sensibly to changed weights;
- route presets produce explainable trade-offs;
- assessment metrics are calculated independently of the composite routing score where appropriate;
- conclusions do not exceed the quality or intended use of the source data;
- the output is described as preliminary corridor screening, not engineering approval.

Consequential methodological choices must respect owner decision boundaries in `AGENTS.md`.

## 8. Reproducibility

For pipeline or analytical changes:

- a clean documented workflow can regenerate outputs from approved source data;
- important configuration is version-controlled;
- source versions/dates or acquisition metadata are retained where available;
- random behavior is avoided or controlled when reproducibility matters;
- generated outputs identify enough configuration/provenance to be traced;
- manual preprocessing is eliminated or explicitly documented.

## 9. Error Handling

Expected failure modes should fail clearly.

Examples include:

- unavailable source service;
- incomplete source download;
- missing required attributes;
- CRS mismatch;
- no valid cells at an endpoint;
- disconnected routing graph/grid;
- empty intersection results where non-empty results are required;
- corrupt or stale generated assets;
- unsupported export state.

Do not convert serious analytical failures into warnings solely to keep a pipeline running.

## 10. Security and Privacy

The baseline project does not require accounts or sensitive user data.

Before completion:

- no credentials, tokens, private paths, or secrets are committed;
- source-service keys, if ever required, are handled through appropriate environment/config mechanisms;
- dependency additions are reasonable and necessary;
- exported or deployed assets contain no unintended local/private metadata;
- adding authentication, sensitive data handling, or a materially different security posture requires owner review.

## 11. Performance

Performance should be measured where it affects product viability.

For analytical work:

- preprocessing time and memory should be reasonable for a portfolio workflow;
- routing performance should be benchmarked on realistic grid sizes;
- repeated work should not be needlessly recomputed when deterministic cached build artifacts are appropriate.

For client-side routing:

- route recalculation must be responsive enough for interactive use;
- browser memory use must be acceptable;
- heavy computation should use a Web Worker or equivalent isolation if appropriate;
- lower-powered devices should not become unusable.

If interactive weighting cannot meet performance goals within the lightweight architecture, reduce scope or use precomputed routing rather than introducing disproportionate infrastructure.

## 12. Accessibility

For user-facing frontend work:

- interactive controls are keyboard reachable;
- focus states are visible;
- control labels and route metrics are understandable without relying only on color;
- text contrast is acceptable;
- icons have accessible names where needed;
- dynamic updates do not make core information inaccessible to assistive technology;
- map-only information is supplemented by textual summaries for key route comparisons.

## 13. Responsive UI Behavior

Validate the application at representative desktop and mobile widths.

Check that:

- the map remains usable;
- route controls remain reachable;
- route summaries do not obscure the primary map interaction;
- content does not overflow or become unreadable;
- constrained mobile layouts preserve the core compare-and-understand workflow rather than exposing every desktop control.

## 14. Visual Verification

For meaningful UI/cartographic changes, inspect the rendered result rather than relying only on tests.

Review:

- route prominence;
- endpoint legibility;
- constraint-layer hierarchy;
- map clutter;
- label readability;
- route comparison clarity;
- selected/hover/focus states;
- legends or explanatory copy;
- empty/loading/error states;
- export controls;
- overall restrained professional appearance.

Avoid a generic admin dashboard, excessive KPI cards, uncontrolled layer lists, or visually aggressive engineering styling.

## 15. Documentation

When work changes reality, update documentation in the same work unit.

At minimum consider:

- `docs/PROJECT_STATE.md`;
- `docs/BACKLOG.md`;
- `docs/ARCHITECTURE.md`;
- `docs/DECISIONS.md` only for consequential decisions;
- source/methodology documentation;
- setup or development instructions;
- limitations and professional-use disclaimer.

Documentation must not claim validation that was not actually performed.

## 16. Deployment Verification

Once deployment exists, relevant release changes should verify:

- the deployed version corresponds to the intended commit/build;
- the application loads without missing assets;
- map styles, tiles/assets, routes, and metadata resolve correctly;
- key interactions work in the deployed environment;
- exports work from the deployed application;
- direct navigation/reload behavior is correct for the hosting setup;
- console/network failures are investigated;
- public URLs do not expose secrets or unintended development artifacts.

A successful local build alone is not evidence of successful deployment.

## Completion Record

For substantial milestones, the completed execution plan should briefly record:

- validation commands actually run;
- important manual checks performed;
- known limitations intentionally remaining;
- any gates not applicable and why;
- final outcome.
