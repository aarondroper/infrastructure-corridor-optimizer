import { describe, expect, it } from "vitest";
import routeAsset from "../public/data/routes.json";
import { parseRouteData, RouteDataError } from "../src/routeData";

describe("parseRouteData", () => {
  it("accepts the tracked canonical route asset", () => {
    const data = parseRouteData(routeAsset);

    expect(data.routes.map((route) => route.preset)).toEqual([
      "shortest",
      "balanced",
      "environmental",
    ]);
    expect(data.endpoints.features).toHaveLength(2);
  });

  it("reports the location of malformed route coordinates", () => {
    const malformed = structuredClone(routeAsset) as Record<string, unknown>;
    const routes = malformed.routes as Array<Record<string, unknown>>;
    const routeGeometry = routes[0].geometry as Record<string, unknown>;
    const line = (routeGeometry.geometry as Record<string, unknown>);
    line.coordinates = [[150.9], [151.0, -32.4]];

    expect(() => parseRouteData(malformed)).toThrowError(
      new RouteDataError("routes[0].geometry.geometry.coordinates[0] must be [longitude, latitude]"),
    );
  });

  it("rejects non-finite route metrics", () => {
    const malformed = structuredClone(routeAsset) as Record<string, unknown>;
    const routes = malformed.routes as Array<Record<string, unknown>>;
    const metrics = (routes[0].metrics as Record<string, unknown>);
    metrics.route_length_km = "95.7";

    expect(() => parseRouteData(malformed)).toThrowError(
      "Invalid route data: routes[0].metrics.route_length_km must be a finite number",
    );
  });
});
