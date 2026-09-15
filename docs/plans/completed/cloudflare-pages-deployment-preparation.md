# Cloudflare Pages deployment preparation

## Objective

Prepare the verified static S1 React/TypeScript + MapLibre MVP for Cloudflare Pages,
validate the exact production artifact and deployment-origin behavior locally, and
document the remaining account-authorized deployment step without claiming a live
deployment.

## Context

The application is a Vite build under `web/`, consumes the compact static route asset
under `web/public/data/routes.json`, uses no server-side code, and has already passed
bounded Chromium verification. Cloudflare Pages is the selected deployment target.

## Approach

1. Inspect Vite, package, asset, and source-path configuration and identify the
   minimal Pages settings.
2. Add only necessary deployment metadata/documentation and, if useful, static
   response headers that are safe for immutable build assets.
3. Build and inspect the complete `web/dist/` artifact; serve it from a production-
   origin-style local server and verify direct/reload paths, asset requests,
   MapLibre basemap behavior, route switching, and exports.
4. Run Python, frontend build, browser, dependency, and repository quality gates.
5. Update architecture, project state, backlog, and application operations; archive
   this plan and commit the coherent preparation change.

## Acceptance criteria

- Exact Cloudflare Pages root directory, build command, and output directory are
  verified from the repository rather than guessed.
- Production output contains the application shell and compact analytical asset,
  with no local filesystem paths, development URLs, or ignored source artifacts.
- A production-style local server verifies root/direct reload behavior, route
  switching, exports, and external basemap request behavior as far as network access
  permits.
- No Functions, Workers, databases, secrets, or raw GIS data are introduced.
- Static asset caching guidance is minimal and safe for the hashed Vite assets.
- Documentation states that live deployment remains pending Cloudflare account
  authorization and gives exact owner instructions.
- Applicable quality gates pass; the plan is archived and the changes are committed.

## Risks and boundaries

- Cloudflare account authorization and GitHub integration are unavailable in this
  workspace; live deployment and public-origin verification cannot be claimed.
- OpenStreetMap tiles remain an external runtime dependency and may be unavailable
  in bounded local probes; this must be distinguished from local application failure.
- No SPA rewrite is required while the app has only the root URL and no client-side
  routes. Do not add one or introduce server-side infrastructure without evidence.

## Outcome

Completed 15 September 2026. The Vite build was verified from `web/` with
`npm run build`, producing `web/dist/` with the shell, hashed CSS/JavaScript,
`_headers`, and the 327,336-byte compact route asset. During release inspection a
local SVTM raster path was found in the generated web asset; the asset builder was
corrected to recursively remove private source/cache/artifact path keys while
retaining non-sensitive provenance. A regression test covers this behavior.

The browser suite passed on an isolated production-preview port with root reload,
static shell/data asset responses, route switching, impact inspection, GeoJSON/CSV
exports, responsive checks at 1280×800, 768×1024, and 390×844, asset failure state,
keyboard focus, and successful OpenStreetMap tile responses. The screenshots were
visually reviewed. Python gates passed in the base and GIS interpreters, and
`npm audit --omit=dev --audit-level=high` reported zero vulnerabilities.

Cloudflare Pages is recorded as the deployment decision. The repository requires no
Functions, Workers, database, secrets, or environment variables. The owner must still
connect the GitHub repository, configure root `web`, command `npm run build`, output
`dist`, deploy from `main`, and return the public URL for final verification.
