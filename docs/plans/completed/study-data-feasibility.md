# Study and Data Feasibility

## Objective

Validate whether the preferred Hunter / New England direction can support a compact,
credible infrastructure-corridor screening case study using reproducibly accessible
public data, and assemble the evidence needed for owner decisions on the study area,
fixed endpoints, and initial constraint set.

## Outcome

Completed on 13 September 2026. The evidence record is
`docs/STUDY_AND_DATA_FEASIBILITY.md`. The preferred direction is feasible, S1
(Upper Hunter to Lake Macquarie / Eraring-area context) is recommended for owner
review, and candidate sources and risks are documented. No consequential study,
endpoint, exclusion, or weighting decision was silently finalized.

## Validation performed

- Read the required governance documents and inspected the actual repository file
  inventory.
- Reviewed official NSW, EnergyCo, Geoscience Australia, and Copernicus source pages
  and service metadata.
- Verified representative live endpoint responses with `curl` using a normal client
  user-agent: Geoscience Australia electricity metadata/WFS, NSW hydrography metadata,
  NSW NPWS Estate metadata/query, and NSW Transport/Elevation multi-CRS metadata.
- Confirmed the NSW source schemas/CRS and recorded the hydrography broad-query timeout,
  EnergyCo GIS ZIP HTTP 202 response, and GDA94/GDA2020 transition risks.
- Ran repository inventory/content checks with `find` and `rg`.
- Attempted `git status`, `git rev-parse`, and Git diff checks; the workspace `.git`
  directory is unusable, so Git state and commit operations could not be verified.

## Known limitations intentionally remaining

- The repository still has no executable code, dependency manifests, test runner,
  data pipeline, or generated assets; code-quality/build gates are not applicable.
- The final scenario, endpoint pair, constraint set, exclusion treatment, and weights
  require owner review.
- Selected-envelope feature/tile coverage and targeted acquisition behavior must be
  validated after the owner selects a scenario.
- The EnergyCo published corridor is contextual evidence, not an optimizer target or
  independent route validation.
