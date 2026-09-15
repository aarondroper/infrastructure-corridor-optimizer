# Visual polish and interface refinement

## Objective

Refine the established static S1 React/TypeScript + MapLibre MVP into a calmer,
denser, more operational professional corridor-screening interface without changing
analytical data, route behavior, exports, architecture, or deployment.

## Context

The current product is functionally complete and deployed. Baseline inspection and
the supplied mockup indicate that the current Georgia-heavy masthead, oversized hero,
detached status block, and default-feeling map controls make the UI read too much like
an editorial landing page. The mockup is reference guidance only; its unimplemented
features are out of scope.

## Approach

1. Establish self-hosted Source Sans 3, a compact type/spacing/color/radius token set,
   and accessible focus/control primitives.
2. Tighten the masthead and integrate status metadata while preserving copy and
   identity.
3. Refine the map workspace, map controls, route status, endpoint labels, strategy
   selection, metrics, inventory details, exports, comparison, and responsive layout.
4. Run production build and browser verification at 1440×900, 1280×800, 768×1024,
   and 390×844; inspect screenshots and confirm all route/export/data behaviors.
5. Review the complete diff, update factual documentation, archive this plan, and
   commit the coherent visual change.

## Acceptance criteria

- Source Sans 3 is bundled locally and used as the interface typeface with tabular
  measurement numerals.
- The map becomes the visual center sooner, with a compact masthead and integrated
  validation status.
- Existing routes, endpoints, metrics, inventories, exports, static assets, and map
  behavior are unchanged.
- Strategy controls, map controls, metrics, focus states, contrast, borders, spacing,
  and responsive layout feel deliberate and operational.
- No new product functionality or analytical/model changes are introduced.
- All applicable quality gates pass and visual evidence is reviewed.

## Risks

- Font metrics may alter wrapping and vertical density at narrow widths.
- MapLibre controls and the camera-synchronized SVG overlay must remain intact.
- Visual changes must not hide essential impact information or weaken keyboard focus.

## Outcome

Completed 15 September 2026. The frontend now bundles Latin Source Sans 3 weights
locally, uses a compact shared visual token set, and presents the existing masthead,
map workspace, strategy panel, metrics, inspection records, comparison, and exports
with a denser operational hierarchy. MapLibre controls, route status, focus states,
and the narrow-screen map caption were refined without changing route data or
analytical behavior.

`npm run build` passed. The production-preview browser suite passed all three tests at
1440×900, 1280×800, 768×1024, and 390×844, including route switching, inspection,
GeoJSON/CSV export, static asset/data loading, error behavior, focus, responsive
overflow, and OpenStreetMap tile responses. Screenshots in the ignored
`web/artifacts/browser-verification/` directory were regenerated after a bounded
basemap-render wait and visually inspected. Base and GIS Python suites each passed
85 tests, `npm audit --omit=dev` reported zero vulnerabilities, and `git diff --check`
passed. The current public Cloudflare origin still serves the prior verified build;
this visual commit was not redeployed during the milestone.
