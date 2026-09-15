import { useEffect, useMemo, useRef, useState } from "react";
import * as maplibregl from "maplibre-gl";
import type { Map } from "maplibre-gl";

type Preset = "shortest" | "balanced" | "environmental";
type AnyRecord = Record<string, any>;
type AppData = {
  scenario: string;
  disclaimer: string;
  endpoints: AnyRecord;
  routes: Array<{
    preset: Preset;
    description: string;
    geometry: AnyRecord;
    metrics: AnyRecord;
    impact_inventory: AnyRecord;
  }>;
  comparison: AnyRecord;
};

const PRESET_LABELS: Record<Preset, string> = {
  shortest: "Shortest",
  balanced: "Balanced",
  environmental: "Environmental",
};

const PRESET_UI_DESCRIPTIONS: Record<Preset, string> = {
  shortest: "Strong preference for route length.",
  balanced: "Balances length, terrain, impacts, and crossings.",
  environmental: "Prioritizes lower environmental sensitivity.",
};

function format(value: number | null | undefined, digits = 1): string {
  return value == null || Number.isNaN(value) ? "—" : value.toFixed(digits);
}

function MapPanel({ data, selected }: { data: AppData; selected: Preset }) {
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<Map | null>(null);
  const [mapInstance, setMapInstance] = useState<Map | null>(null);
  const [, setCameraRevision] = useState(0);
  const selectedRoute = data.routes.find((route) => route.preset === selected);

  useEffect(() => {
    if (!container.current) return;
    const allCoordinates = data.routes.flatMap((route) => route.geometry.geometry.coordinates);
    const endpointCoordinates = data.endpoints.features.map((feature: AnyRecord) => feature.geometry.coordinates);
    const bounds = new maplibregl.LngLatBounds();
    [...allCoordinates, ...endpointCoordinates].forEach(([lng, lat]) => bounds.extend([lng, lat]));
    const style: AnyRecord = {
      version: 8,
      sources: {
        osm: {
          type: "raster",
          tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
          tileSize: 256,
          attribution: "© OpenStreetMap contributors",
        },
      },
      layers: [{ id: "osm", type: "raster", source: "osm" }],
    };
    const instance = new maplibregl.Map({ container: container.current, style: style as any, bounds, fitBoundsOptions: { padding: 72 } });
    instance.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    const updateOverlay = () => setCameraRevision((revision) => revision + 1);
    const resizeObserver = new ResizeObserver(() => { instance.resize(); updateOverlay(); });
    resizeObserver.observe(container.current);
    instance.on("load", () => { container.current?.parentElement?.setAttribute("data-map-layers", "basemap,route-overlay,endpoints,endpoint-labels"); updateOverlay(); });
    instance.on("move", updateOverlay);
    instance.on("resize", updateOverlay);
    map.current = instance;
    setMapInstance(instance);
    return () => { resizeObserver.disconnect(); instance.off("move", updateOverlay); instance.off("resize", updateOverlay); instance.remove(); map.current = null; setMapInstance(null); };
  }, [data]);

  const projectedRoutes = mapInstance ? data.routes.map((route) => ({ ...route, points: route.geometry.geometry.coordinates.map(([lng, lat]: number[]) => { const point = mapInstance.project([lng, lat]); return `${point.x},${point.y}`; }).join(" ") })) : [];
  const projectedEndpoints = mapInstance ? data.endpoints.features.map((feature: AnyRecord) => ({ ...feature, point: mapInstance.project(feature.geometry.coordinates) })) : [];
  return <div className="map-wrap" data-map-layers="loading">
    <div ref={container} className="map" aria-label={`Map showing the ${PRESET_LABELS[selected]} route`} />
    {mapInstance && <svg className="route-overlay" role="img" aria-label="Precomputed route overlay" data-rendered-route-features={projectedRoutes.length} data-rendered-endpoint-features={projectedEndpoints.length}>
      {projectedRoutes.filter((route) => route.preset !== selected).map((route) => <polyline key={`${route.preset}-muted`} className={`route-line route-line-${route.preset}`} data-preset={route.preset} points={route.points} />)}
      {projectedRoutes.filter((route) => route.preset === selected).map((route) => <g key={`${route.preset}-selected`}><polyline className="route-line route-line-casing" data-preset={route.preset} points={route.points} /><polyline className={`route-line route-line-selected route-line-selected-${route.preset}`} data-preset={route.preset} points={route.points} /></g>)}
      {projectedEndpoints.map((endpoint: AnyRecord) => <g key={endpoint.properties.name} className="route-endpoint"><circle cx={endpoint.point.x} cy={endpoint.point.y} r="6" /><text x={endpoint.point.x} y={endpoint.point.y + (endpoint.properties.role === "destination" ? -10 : 21)}>{endpoint.properties.name}</text></g>)}
    </svg>}
    <div className="map-legend" aria-label="Candidate routes"><span className="map-legend-heading">Candidate routes</span>{data.routes.map((route) => <div className={`map-legend-item ${route.preset === selected ? "selected" : ""}`} key={route.preset}><span className={`route-swatch route-swatch-${route.preset}`} aria-hidden="true" /><span>{PRESET_LABELS[route.preset]}</span>{route.preset === selected && <span className="legend-selected">Selected</span>}</div>)}</div>
    <div className="map-caption">S1 · 100 m analysis grid · route centerlines shown for preliminary screening</div>{selectedRoute && <div className="map-badge" role="status"><span className={`route-swatch route-swatch-${selected}`} aria-hidden="true" />{PRESET_LABELS[selected]} route selected</div>}
  </div>;
}

function download(name: string, content: string, type: string) {
  const link = document.createElement("a");
  link.href = URL.createObjectURL(new Blob([content], { type }));
  link.download = name;
  link.click();
  URL.revokeObjectURL(link.href);
}

function csvCell(value: unknown): string {
  const text = value == null ? "" : String(value);
  return /[",\n]/.test(text) ? `"${text.split('"').join('""')}"` : text;
}

function StrategyPanel({ data, selected, onSelect }: { data: AppData; selected: Preset; onSelect: (preset: Preset) => void }) {
  return <aside className="strategy-rail" aria-label="Route strategy controls">
    <div className="rail-heading">
      <h2>Route strategy</h2>
      <p>Select a precomputed route to inspect its trade-offs.</p>
    </div>
    <div className="preset-list">{data.routes.map((item) => <button className={`preset ${item.preset === selected ? "selected" : ""}`} key={item.preset} onClick={() => onSelect(item.preset)} aria-pressed={item.preset === selected}>
      <span className={`route-swatch route-swatch-${item.preset}`} aria-hidden="true" /><span className="preset-copy"><strong>{PRESET_LABELS[item.preset]}</strong><small>{PRESET_UI_DESCRIPTIONS[item.preset]}</small></span>
    </button>)}</div>
  </aside>;
}

function AssessmentPanel({ route, selected, csv }: { route: AppData["routes"][number]; selected: Preset; csv: string }) {
  const inv = route.impact_inventory;
  const native = inv.native_vegetation ?? {};
  return <aside className="assessment-panel panel" aria-label="Route summary">
    <div className="panel-heading">
      <p className="panel-kicker">Route summary</p>
      <h2><span className={`route-swatch route-swatch-${selected}`} aria-hidden="true" />{PRESET_LABELS[selected]} route</h2>
    </div>
    <div className="selected-summary">
      <div className="metric-primary"><span>Selected route</span><strong>{format(route.metrics.route_length_km, 2)} km</strong></div>
      <div className="metric-grid">
        <div><span>Mean slope</span><strong>{format(route.metrics.slope_mean_degrees)}°</strong></div>
        <div><span>Native vegetation</span><strong>{native.native_vegetation_cell_count ?? "—"} cells</strong></div>
        <div><span>Hydroline crossings</span><strong>{inv.hydrography_line?.crossing_feature_count ?? "—"}</strong></div>
        <div><span>Major roads</span><strong>{inv.roads?.major_road_intersection_count ?? "—"}</strong></div>
      </div>
      <div className="inventory-summary"><span>Feature inventory</span><div>
        {["Protected areas", "Hydro areas", "Road features", "Rail features"].map((label, index) => {
          const count = [inv.protected_land?.intersected_feature_count, inv.hydrography_area?.interaction_feature_count, inv.roads?.intersected_feature_count, inv.railways?.crossing_feature_count][index];
          return <span key={label}><strong>{count ?? "—"}</strong> {label}</span>;
        })}
      </div></div>
      <div className="actions"><button onClick={() => download(`${selected}-route.geojson`, JSON.stringify(route.geometry, null, 2), "application/geo+json")}>Export GeoJSON</button><button onClick={() => download(`${selected}-crossings.csv`, csv, "text/csv")}>Export crossings CSV</button></div>
      <div className="inventory-details"><span>Inspect intersected records</span>{Object.entries(inv).map(([component, layer]) => {
        const entries = (layer.features ?? []).slice(0, 6);
        const classes = (layer.classes ?? []).filter((entry: AnyRecord) => entry.value > 0).slice(0, 6);
        return <details key={component}><summary>{component.split("_").join(" ")} <b>{layer.intersected_feature_count ?? layer.native_vegetation_cell_count ?? 0}</b></summary><ul>
          {entries.map((entry: AnyRecord) => <li key={`${component}-${entry.source_object_id}`}>{entry.properties?.roadnamebase ?? entry.properties?.hydroname ?? entry.properties?.NAME ?? entry.source_object_id}{entry.major_road ? " · major" : ""}</li>)}
          {classes.map((entry: AnyRecord) => <li key={`${component}-${entry.value}`}>{entry.PCTName ?? `PCT ${entry.value}`} · {entry.route_cell_count} cells</li>)}
        </ul></details>;
      })}</div>
    </div>
  </aside>;
}

function ComparisonStrip({ data, selected, onSelect }: { data: AppData; selected: Preset; onSelect: (preset: Preset) => void }) {
  return <section className="comparison-strip" aria-labelledby="comparison-heading">
    <div className="comparison-title"><h2 id="comparison-heading">Route comparison</h2><p>Evidence at a glance</p></div>
    <div className="comparison-table"><div className="table-head"><span>Preset</span><span>Length</span><span>Native veg.</span><span>Hydroline</span><span>Major roads</span></div>{data.routes.map((item) => { const itemInv = item.impact_inventory; return <button className={`table-row ${item.preset === selected ? "active" : ""}`} key={item.preset} onClick={() => onSelect(item.preset)} aria-pressed={item.preset === selected}><span className="comparison-preset"><span className={`route-swatch route-swatch-${item.preset}`} aria-hidden="true" />{PRESET_LABELS[item.preset]}</span><span>{format(item.metrics.route_length_km, 2)} km</span><span>{itemInv.native_vegetation?.native_vegetation_cell_count ?? "—"}</span><span>{itemInv.hydrography_line?.crossing_feature_count ?? "—"}</span><span>{itemInv.roads?.major_road_intersection_count ?? "—"}</span></button>; })}</div>
  </section>;
}

function App() {
  const [data, setData] = useState<AppData | null>(null);
  const [selected, setSelected] = useState<Preset>("balanced");
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { fetch("/data/routes.json").then((response) => { if (!response.ok) throw new Error(`Asset request failed (${response.status})`); return response.json(); }).then(setData).catch((reason: Error) => setError(reason.message)); }, []);
  const route = useMemo(() => data?.routes.find((item) => item.preset === selected), [data, selected]);
  if (error) return <main className="state"><h1>Corridor assets unavailable</h1><p>{error}</p></main>;
  if (!data || !route) return <main className="state"><p>Loading validated S1 routes…</p></main>;
  const inv = route.impact_inventory;
  const inventoryCsvRows = Object.entries(inv).flatMap(([component, layer]) => [
    ...(layer.features ?? []).map((feature: AnyRecord) => [selected, component, feature.source_object_id, feature.intersection_length_m ?? "", feature.major_road ?? "", feature.properties?.roadnamebase ?? feature.properties?.hydroname ?? feature.properties?.NAME ?? ""]),
    ...(layer.classes ?? []).filter((entry: AnyRecord) => entry.value > 0).map((entry: AnyRecord) => [selected, component, entry.value, "", "", entry.PCTName ?? ""]),
  ]);
  const csv = [["route_preset", "component", "source_object_id", "intersection_length_m", "major_road", "source_name"], ...inventoryCsvRows].map((row) => row.map(csvCell).join(",")).join("\n");
  return <main className="app-frame">
    <header className="app-header">
      <div className="brand"><h1>Infrastructure Corridor Optimizer</h1><p>Preliminary corridor screening · Hunter / New England, NSW · Scenario {data.scenario}</p></div>
      <div className="status" role="status" aria-label="Route asset status"><span className="status-label">Offline route assets</span><span className="status-value">Validated · source-backed</span></div>
    </header>
    <section className="app-shell" aria-label="Corridor route workspace">
      <StrategyPanel data={data} selected={selected} onSelect={setSelected} />
      <section className="map-column" aria-label="Route map"><MapPanel data={data} selected={selected} /></section>
      <AssessmentPanel route={route} selected={selected} csv={csv} />
    </section>
    <ComparisonStrip data={data} selected={selected} onSelect={setSelected} />
    <footer><p>{data.disclaimer}</p><p>Base map © OpenStreetMap contributors · approved environmental and crossing layers are summarized in the route assessment.</p></footer>
  </main>;
}

export { App };
