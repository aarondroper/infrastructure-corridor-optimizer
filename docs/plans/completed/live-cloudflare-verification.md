# Live Cloudflare deployment verification

## Objective

Verify the public Cloudflare deployment of the accepted static S1 React/TypeScript +
MapLibre MVP against the committed production artifact, without changing product
features or analytical assumptions.

## Context

The owner supplied `nfrastructure-corridor-optimizer.aaronroper.workers.dev`, whose
hostname omits the initial `i` and does not resolve. The likely corrected hostname
`infrastructure-corridor-optimizer.aaronroper.workers.dev` resolves and serves the
expected application shell. The deployment documentation selected Cloudflare Pages;
the final verification must record whether this `workers.dev` hostname is an alias or
another Cloudflare delivery mechanism.

## Approach and acceptance criteria

1. Compare live shell, hashed assets, compact route asset, and response metadata with
   the local commit `6c4d543` build.
2. Run the existing Playwright product suite against the public origin at desktop,
   laptop, tablet, and mobile sizes, including route switching, inspection, exports,
   reload, focus, error capture, and basemap requests.
3. Run bounded direct HTTP checks for asset status/content types/cache headers and
   absence of local/development references.
4. Fix only ordinary deployment/frontend defects, rerun quality gates, and document
   the actual public hostname and deployment evidence.
5. Update project state/backlog/architecture/deployment documentation, archive this
   plan, and commit the verified reality. Do not claim a provider-specific build or
   commit identity beyond available evidence.

## Risks and boundaries

- The supplied hostname may be a typo or may identify a different Cloudflare product;
  this must be distinguished from the documented Pages target.
- Cloudflare response headers may not expose the source commit; matching immutable
  asset bytes and filenames is strong artifact evidence but not account metadata.
- OpenStreetMap remains an external runtime dependency and may fail independently of
  the deployed application.

## Outcome

Completed 15 September 2026. The supplied hostname was missing the initial `i`; the
corrected `workers.dev` origin resolved and served the expected static application.
The public shell, compact route JSON, hashed JavaScript, and hashed CSS matched the
local production artifact for commit `6c4d543` byte-for-byte. Public-origin Playwright
verification passed all three tests at desktop, laptop, tablet, and mobile sizes,
including route switching, inspection, exports, reload, focus, error capture, and
basemap responses. Strict network capture found no console/page errors or genuine
failed requests; obsolete OSM tile cancellations were expected during camera settling.
An independent live-browser probe observed 36 OSM tile responses, all HTTP 200, with
no blocked-response header, failures, or console errors.

Cloudflare cache headers matched the checked-in policy: immutable hashed assets and
revalidatable route data. The public hostname is `workers.dev`, so HTTP evidence alone
cannot identify a Pages project name, distinguish a Worker alias from Pages delivery,
or expose account-linked source commit metadata. This caveat is recorded in the
deployment documentation and project state. No product or analytical changes were
made.
