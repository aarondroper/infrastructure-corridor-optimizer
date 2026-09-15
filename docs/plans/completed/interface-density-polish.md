# Interface density and component polish

## Objective

Refine the approved Infrastructure Corridor Optimizer application shell so its
strategy rail, assessment panel, map overlays, comparison dock, header, and footer
feel denser and more operational without changing layout architecture, analytical
methodology, route data, or deployment.

## Context

Commit `f1480f0` established the approved desktop `strategy | map | assessment` shell
and stacked responsive modes. Visual review identified remaining verbosity in the
strategy options, excessive panel weight, generic-looking overlay labels, and a
comparison region that still read like a webpage table.

## Approach

1. Preserve Source Sans 3, the cream/teal/orange system, map dimensions and rendering,
   route assets, metrics, inventories, exports, and semantic controls.
2. Shorten only the UI presentation copy for the three existing strategies.
3. Tighten panel spacing and hierarchy, make counts and accordions scan cleanly, and
   reduce export-button emphasis without removing content.
4. Refine existing map chip/caption surfaces, header alignment, comparison-dock
   hierarchy, selected-row indication, and footer prominence.
5. Run all analytical/frontend/browser gates and inspect screenshots at every required
   viewport, then update documentation and archive this plan.

## Acceptance criteria

- The approved shell and responsive ordering remain unchanged.
- All current route strategy choices, metrics, inventory records, map endpoints,
  route overlays, exports, error state, and OSM tile behavior continue to work.
- Strategy descriptions are concise; route length leads the assessment hierarchy;
  utilities and record accordions are secondary but complete.
- Map metadata and comparison rows read as integrated application UI.
- No analytical, data, route, deployment, or product-scope changes are introduced.
- Python suites, production build, browser suite, npm audit, and visual review pass.

## Risks

- Over-compression could reduce readability or tap targets.
- Utility/accordion movement must preserve discoverability and keyboard behavior.
- Screenshot timing and external basemap loading can otherwise misrepresent the visual
  result, so evidence waits for bounded tile rendering.

## Outcome

Implemented 15 September 2026. The approved shell remains intact while strategy copy,
panel spacing, metric hierarchy, inventory counts, accordions, exports, map metadata,
header alignment, comparison dock, and footer treatment were tightened. The current
public deployment was intentionally not changed.
