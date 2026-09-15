# Application shell and layout refactor

## Objective

Refactor the established static S1 React/TypeScript + MapLibre MVP from a webpage-like
composition into a compact professional geospatial decision-support shell without
changing analytical data, route behavior, exports, map architecture, or deployment.

## Context

The previous visual-polish milestone improved typography, palette, controls, and
component styling, but the large editorial introduction and appended map/panel layout
still delay the application and waste viewport space. The supplied mockup is layout
inspiration only; mockup-only controls and analytical content remain out of scope.

## Approach

1. Preserve the Source Sans 3 system, map implementation, route asset semantics, and
   existing accessibility behavior while removing the marketing headline.
2. Reorganize existing markup into a compact application header, desktop strategy rail,
   dominant map canvas, assessment panel, and bottom comparison strip.
3. Define intentional desktop, laptop, tablet, and mobile layout modes with controlled
   density and no horizontal overflow.
4. Extend browser assertions only where needed to protect the new shell hierarchy and
   existing interactions, then validate at all established viewports with screenshots.
5. Review the diff for analytical/functional changes, update factual documentation,
   archive this plan, and commit the completed refactor.

## Acceptance criteria

- The slogan is removed and the header communicates project, study context, scenario,
  and source-backed validation compactly.
- Desktop layout presents strategy → map → assessment immediately below the header;
  the map is the dominant element and comparison is compact and visible.
- Tablet and mobile layouts remain readable, usable, and free of horizontal overflow.
- Existing route switching, selected states, map overlays/endpoints, metrics, impact
  inspection, GeoJSON export, CSV export, error state, and OSM requests still pass.
- Route JSON, analytical values, endpoint coordinates, and MapLibre/SVG architecture
  are unchanged.
- Production build, Python gates, browser tests, visual screenshots, and dependency
  audit pass where available.

## Risks

- Moving assessment content into a narrower panel could create unwanted wrapping or
  excessive scrolling.
- Changing map height and container sizing must preserve ResizeObserver/camera overlay
  synchronization.
- Mobile ordering must keep strategy, map, assessment, comparison, and exports usable
  without hiding essential content.

## Outcome

Completed 15 September 2026. The slogan-led page composition was replaced with a
compact application shell: a project/context header, desktop strategy rail, dominant
map, right-side route assessment, and integrated bottom comparison strip. Tablet uses
map-first stacking; mobile uses strategy-first stacking while keeping the map,
assessment, details, exports, and comparison accessible. The prior Source Sans 3
system, cream/teal/orange identity, MapLibre camera, SVG route overlay, endpoint
coordinates, route data, impact inventories, and exports were preserved.

The production build and browser suite passed. Browser checks covered route switching
through both strategy controls and comparison rows, selected states, map/endpoints,
inspection, GeoJSON/CSV export, error handling, focus styling, static assets, OSM
responses, and no horizontal overflow at 1440×900, 1280×800, 768×1024, and 390×844.
The resulting screenshots in ignored `web/artifacts/browser-verification/` were
visually inspected. Python base/GIS gates remain unchanged and were rerun after the
layout implementation before completion; no analytical or deployment behavior was
changed. `npm audit --omit=dev` reported zero vulnerabilities.
