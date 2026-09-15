# Repository working guide

This repository contains the Infrastructure Corridor Optimizer: a preliminary
geospatial corridor-screening application and its reproducible offline build.

Before editing, read `README.md` and the technical documents relevant to the
change. Inspect the actual repository, generated assets, and Git status rather
than relying on documentation alone. Preserve unrelated working-tree changes.

## Project invariants

- `config/model.json` is the source of analytical configuration.
- Route outputs are generated from the configured model and validated data; they
  must not be manually drawn or silently altered for presentation.
- The published application consumes generated `web/public/data/routes.json`.
- Large GIS source artifacts, caches, staging directories, and build outputs stay
  outside Git.
- Changes to the model, source interpretation, grid, route generation, metrics,
  or export schema require corresponding tests and documentation updates.
- The application is for preliminary corridor screening, not engineering,
  permitting, cadastral, or construction approval.

## Contribution workflow

Keep changes focused and commits coherent. Run the relevant Python tests,
frontend build, browser checks, and data validation for the area changed. Review
the complete diff for stale documentation, unintended generated files, broken
paths, and unsupported claims before committing. Update durable documentation when
repository behavior or reproducibility instructions change.
