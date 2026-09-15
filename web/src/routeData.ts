export const PRESETS = ["shortest", "balanced", "environmental"] as const;

export type Preset = (typeof PRESETS)[number];
export type JsonValue = null | boolean | number | string | JsonValue[] | JsonObject;
export type JsonObject = { [key: string]: JsonValue };
export type Coordinate = [number, number];

export type RouteFeature = JsonObject & {
  type: "Feature";
  properties: JsonObject & { preset: Preset };
  geometry: JsonObject & { type: "LineString"; coordinates: Coordinate[] };
};

export type EndpointFeature = JsonObject & {
  type: "Feature";
  properties: JsonObject & { role: "origin" | "destination"; name: string };
  geometry: JsonObject & { type: "Point"; coordinates: Coordinate };
};

export type EndpointCollection = JsonObject & {
  type: "FeatureCollection";
  features: EndpointFeature[];
};

export type RouteMetrics = JsonObject & {
  path_cell_count: number;
  route_length_km: number;
  terrain_normalized_mean: number;
  terrain_normalized_max: number;
  slope_mean_degrees: number;
  slope_max_degrees: number;
  diagnostics: JsonObject;
  endpoint_cells: JsonObject;
};

export type InventoryFeature = JsonObject & {
  source_object_id: number;
  intersection_length_m?: number;
  intersection_dimension?: number;
  properties: JsonObject;
  major_road?: boolean;
};

export type InventoryClass = JsonObject & {
  value: number;
  route_cell_count: number;
  PCTName?: string;
};

export type InventoryLayer = JsonObject & {
  component: string;
  intersected_feature_count?: number;
  interaction_feature_count?: number;
  crossing_feature_count?: number;
  major_road_intersection_count?: number;
  native_vegetation_cell_count?: number;
  features?: InventoryFeature[];
  classes?: InventoryClass[];
};

export type ImpactInventory = { [component: string]: InventoryLayer };

export type RouteRecord = JsonObject & {
  preset: Preset;
  description: string;
  geometry: RouteFeature;
  metrics: RouteMetrics;
  impact_inventory: ImpactInventory;
};

export type ComparisonRoute = JsonObject & {
  preset: Preset;
  route_length_km: number;
  slope_mean_degrees: number;
};

export type Comparison = JsonObject & {
  baseline: Preset;
  routes: ComparisonRoute[];
};

export type RouteData = JsonObject & {
  schema_version: number;
  format: string;
  scenario: string;
  display_crs_epsg: number;
  endpoints: EndpointCollection;
  routes: RouteRecord[];
  comparison: Comparison;
  disclaimer: string;
  provenance: JsonObject;
};

const INVENTORY_COMPONENTS = [
  "protected_land",
  "hydrography_line",
  "hydrography_area",
  "roads",
  "railways",
  "native_vegetation",
] as const;

const REQUIRED_METRICS = [
  "path_cell_count",
  "route_length_km",
  "terrain_normalized_mean",
  "terrain_normalized_max",
  "slope_mean_degrees",
  "slope_max_degrees",
] as const;

export class RouteDataError extends Error {
  constructor(detail: string) {
    super(`Invalid route data: ${detail}`);
    this.name = "RouteDataError";
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function record(value: unknown, path: string): Record<string, unknown> {
  if (!isRecord(value)) throw new RouteDataError(`${path} must be an object`);
  return value;
}

function array(value: unknown, path: string): unknown[] {
  if (!Array.isArray(value)) throw new RouteDataError(`${path} must be an array`);
  return value;
}

function string(value: unknown, path: string): string {
  if (typeof value !== "string" || value.trim() === "") {
    throw new RouteDataError(`${path} must be a non-empty string`);
  }
  return value;
}

function finiteNumber(value: unknown, path: string): number {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new RouteDataError(`${path} must be a finite number`);
  }
  return value;
}

function boolean(value: unknown, path: string): boolean {
  if (typeof value !== "boolean") throw new RouteDataError(`${path} must be a boolean`);
  return value;
}

function expected<T>(value: unknown, actual: T, path: string): T {
  if (value !== actual) throw new RouteDataError(`${path} must be ${String(actual)}`);
  return actual;
}

function coordinates(value: unknown, path: string, minimumLength: number): Coordinate[] {
  const values = array(value, path);
  if (values.length < minimumLength) {
    throw new RouteDataError(`${path} must contain at least ${minimumLength} coordinate pairs`);
  }
  return values.map((value, index) => {
    const pair = array(value, `${path}[${index}]`);
    if (pair.length !== 2) throw new RouteDataError(`${path}[${index}] must be [longitude, latitude]`);
    return [
      finiteNumber(pair[0], `${path}[${index}][0]`),
      finiteNumber(pair[1], `${path}[${index}][1]`),
    ];
  });
}

function point(value: unknown, path: string): Coordinate {
  const pair = array(value, path);
  if (pair.length !== 2) throw new RouteDataError(`${path} must be [longitude, latitude]`);
  return [finiteNumber(pair[0], `${path}[0]`), finiteNumber(pair[1], `${path}[1]`)];
}

function validatePointFeature(value: unknown, path: string): EndpointFeature {
  const feature = record(value, path);
  expected(feature.type, "Feature", `${path}.type`);
  const properties = record(feature.properties, `${path}.properties`);
  const role = properties.role;
  if (role !== "origin" && role !== "destination") {
    throw new RouteDataError(`${path}.properties.role must be origin or destination`);
  }
  const geometry = record(feature.geometry, `${path}.geometry`);
  expected(geometry.type, "Point", `${path}.geometry.type`);
  const pointCoordinates = point(geometry.coordinates, `${path}.geometry.coordinates`);
  return {
    ...feature,
    type: "Feature",
    properties: { ...properties, role, name: string(properties.name, `${path}.properties.name`) },
    geometry: { ...geometry, type: "Point", coordinates: pointCoordinates },
  } as EndpointFeature;
}

function validateEndpoints(value: unknown): EndpointCollection {
  const endpoints = record(value, "endpoints");
  expected(endpoints.type, "FeatureCollection", "endpoints.type");
  const features = array(endpoints.features, "endpoints.features");
  if (features.length !== 2) throw new RouteDataError("endpoints.features must contain origin and destination");
  const validated = features.map((feature, index) => validatePointFeature(feature, `endpoints.features[${index}]`));
  const roles = new Set(validated.map((feature) => feature.properties.role));
  if (roles.size !== 2 || !roles.has("origin") || !roles.has("destination")) {
    throw new RouteDataError("endpoints.features must contain one origin and one destination");
  }
  return { ...endpoints, type: "FeatureCollection", features: validated } as EndpointCollection;
}

function validateFeatureEntries(value: unknown, path: string): InventoryFeature[] {
  return array(value, path).map((entry, index) => {
    const feature = record(entry, `${path}[${index}]`);
    const result = {
      ...feature,
      source_object_id: finiteNumber(feature.source_object_id, `${path}[${index}].source_object_id`),
      properties: record(feature.properties, `${path}[${index}].properties`),
    } as InventoryFeature;
    if (feature.intersection_length_m !== undefined) {
      finiteNumber(feature.intersection_length_m, `${path}[${index}].intersection_length_m`);
    }
    if (feature.intersection_dimension !== undefined) {
      finiteNumber(feature.intersection_dimension, `${path}[${index}].intersection_dimension`);
    }
    if (feature.major_road !== undefined) boolean(feature.major_road, `${path}[${index}].major_road`);
    return result;
  });
}

function validateClassEntries(value: unknown, path: string): InventoryClass[] {
  return array(value, path).map((entry, index) => {
    const item = record(entry, `${path}[${index}]`);
    const result = {
      ...item,
      value: finiteNumber(item.value, `${path}[${index}].value`),
      route_cell_count: finiteNumber(item.route_cell_count, `${path}[${index}].route_cell_count`),
    } as InventoryClass;
    if (item.PCTName !== undefined) string(item.PCTName, `${path}[${index}].PCTName`);
    return result;
  });
}

function validateInventory(value: unknown, path: string): ImpactInventory {
  const inventory = record(value, path);
  const result: Record<string, InventoryLayer> = {};
  for (const component of INVENTORY_COMPONENTS) {
    const layer = record(inventory[component], `${path}.${component}`);
    string(layer.component, `${path}.${component}.component`);
    const collection = component === "native_vegetation" ? "classes" : "features";
    if (!Array.isArray(layer[collection])) {
      throw new RouteDataError(`${path}.${component}.${collection} must be an array`);
    }
    if (layer.features !== undefined) {
      layer.features = validateFeatureEntries(layer.features, `${path}.${component}.features`);
    }
    if (layer.classes !== undefined) {
      layer.classes = validateClassEntries(layer.classes, `${path}.${component}.classes`);
    }
    for (const key of ["intersected_feature_count", "interaction_feature_count", "crossing_feature_count", "native_vegetation_cell_count"]) {
      if (layer[key] !== undefined) finiteNumber(layer[key], `${path}.${component}.${key}`);
    }
    result[component] = layer as InventoryLayer;
  }
  return { ...inventory, ...result } as ImpactInventory;
}

function validateRoute(value: unknown, index: number): RouteRecord {
  const path = `routes[${index}]`;
  const route = record(value, path);
  const preset = route.preset;
  if (!PRESETS.includes(preset as Preset)) throw new RouteDataError(`${path}.preset is not an approved strategy`);
  const geometry = record(route.geometry, `${path}.geometry`);
  expected(geometry.type, "Feature", `${path}.geometry.type`);
  const properties = record(geometry.properties, `${path}.geometry.properties`);
  expected(properties.preset, preset, `${path}.geometry.properties.preset`);
  const line = record(geometry.geometry, `${path}.geometry.geometry`);
  expected(line.type, "LineString", `${path}.geometry.geometry.type`);
  const metrics = record(route.metrics, `${path}.metrics`);
  for (const metric of REQUIRED_METRICS) finiteNumber(metrics[metric], `${path}.metrics.${metric}`);
  const diagnostics = record(metrics.diagnostics, `${path}.metrics.diagnostics`);
  boolean(diagnostics.route_is_available, `${path}.metrics.diagnostics.route_is_available`);
  boolean(diagnostics.continuity_validated, `${path}.metrics.diagnostics.continuity_validated`);
  const endpointCells = record(metrics.endpoint_cells, `${path}.metrics.endpoint_cells`);
  point(endpointCells.origin, `${path}.metrics.endpoint_cells.origin`);
  point(endpointCells.destination, `${path}.metrics.endpoint_cells.destination`);
  return {
    ...route,
    preset,
    description: string(route.description, `${path}.description`),
    geometry: {
      ...geometry,
      type: "Feature",
      properties: { ...properties, preset },
      geometry: { ...line, type: "LineString", coordinates: coordinates(line.coordinates, `${path}.geometry.geometry.coordinates`, 2) },
    } as RouteFeature,
    metrics: { ...metrics, diagnostics, endpoint_cells: endpointCells } as RouteMetrics,
    impact_inventory: validateInventory(route.impact_inventory, `${path}.impact_inventory`),
  } as RouteRecord;
}

function validateComparison(value: unknown): Comparison {
  const comparison = record(value, "comparison");
  if (!PRESETS.includes(comparison.baseline as Preset)) throw new RouteDataError("comparison.baseline is not an approved strategy");
  const routes = array(comparison.routes, "comparison.routes");
  if (routes.length !== PRESETS.length) throw new RouteDataError("comparison.routes must contain all approved strategies");
  const validated = routes.map((value, index) => {
    const route = record(value, `comparison.routes[${index}]`);
    if (!PRESETS.includes(route.preset as Preset)) throw new RouteDataError(`comparison.routes[${index}].preset is not approved`);
    finiteNumber(route.route_length_km, `comparison.routes[${index}].route_length_km`);
    finiteNumber(route.slope_mean_degrees, `comparison.routes[${index}].slope_mean_degrees`);
    return route as ComparisonRoute;
  });
  const presets = new Set(validated.map((route) => route.preset));
  if (presets.size !== PRESETS.length || PRESETS.some((preset) => !presets.has(preset))) {
    throw new RouteDataError("comparison.routes must contain shortest, balanced, and environmental strategies");
  }
  return { ...comparison, baseline: comparison.baseline as Preset, routes: validated } as Comparison;
}

export function parseRouteData(payload: unknown): RouteData {
  const data = record(payload, "root");
  expected(data.schema_version, 1, "schema_version");
  expected(data.format, "ico-static-route-assets", "format");
  expected(data.scenario, "S1", "scenario");
  finiteNumber(data.display_crs_epsg, "display_crs_epsg");
  const endpoints = validateEndpoints(data.endpoints);
  const routes = array(data.routes, "routes");
  if (routes.length !== PRESETS.length) throw new RouteDataError("routes must contain all approved strategies");
  const validatedRoutes = routes.map(validateRoute);
  const presets = new Set(validatedRoutes.map((route) => route.preset));
  if (presets.size !== PRESETS.length || PRESETS.some((preset) => !presets.has(preset))) {
    throw new RouteDataError("routes must contain shortest, balanced, and environmental strategies");
  }
  return {
    ...data,
    schema_version: 1,
    format: "ico-static-route-assets",
    scenario: "S1",
    display_crs_epsg: data.display_crs_epsg as number,
    endpoints,
    routes: validatedRoutes,
    comparison: validateComparison(data.comparison),
    disclaimer: string(data.disclaimer, "disclaimer"),
    provenance: record(data.provenance, "provenance"),
  } as RouteData;
}
