# Map comparison and interaction-state polish

## Objective

Strengthen the visual comparison of the three existing S1 route presets while
preserving the approved application shell, route assets, analytical behavior, and
deployment architecture.

## Context

The current SVG overlay technically renders all three precomputed routes, but the
unselected routes share one muted style. Strategy-button focus can also be confused
with analytical selection, and route identity is not carried consistently into the
comparison dock.

## Approach

1. Add route-specific, restrained SVG line treatments and a compact map legend.
2. Reuse the route identity in strategy controls, assessment context, and comparison
   rows through small inline swatches.
3. Separate selected, hover, focus, and selected-plus-focus states without changing
   keyboard semantics.
4. Make only low-risk typography/width refinements supported by rendered inspection.
5. Validate all existing interactions, exports, route assets, basemap requests,
   responsive viewports, and unchanged analytical values.

## Acceptance criteria

- All three existing route geometries remain visible simultaneously and the selected
  route is clearly dominant.
- The legend swatches match the actual map line treatments and identifies selection.
- Strategy focus is visible but does not resemble the selected state.
- Strategy rail, assessment panel, map, and comparison dock share route identities.
- Existing route switching, metrics, inventories, exports, and responsive behavior
  remain unchanged.
- Production build, browser suite, required Python suites, and npm audit pass.
- Screenshots at 1440×900, 1280×800, 768×1024, and 390×844 are visually inspected.

## Risks

- Additional lines may increase map clutter, especially on narrow screens.
- Route-specific colors must remain distinguishable over the OSM basemap without
  becoming decorative or relying only on hue.
- Focus styling must remain accessible while staying visually separate from selection.

## Validation

Run the repository quality gates, production-preview browser tests, and visual review
of all four established viewports. Confirm route asset bytes and export behavior are
unchanged by the frontend-only implementation.

## Outcome

Implemented 15 September 2026. All three existing route centerlines now remain visible
with restrained route-specific line styles, a selected-route emphasis, and a compact
legend. Route identity is shared with the strategy rail, assessment heading, map
status, and comparison dock. Focus and selected states are visually distinct, while
the approved shell, analytical assets, metrics, inventories, exports, and responsive
behavior remain unchanged. Production-preview browser, Python, build, and audit gates
passed; the public deployment was intentionally not changed.
