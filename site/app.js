// OpenGridPK - static site bootstrap.
// Reads canonical voltage classes from data/reference/voltage_classes.json
// (the same file the Python pipeline reads), wires up MapLibre layers, the
// legend toggles, and click popups.

// Pipeline copies data/reference/voltage_classes.json into site/data/ so the
// site is self-contained and works regardless of repo layout / Pages config.
const VOLTAGE_CLASSES_URL = "data/voltage_classes.json";
const META_URL = "data/meta.json";
const PK_BBOX = [60.8, 23.5, 77.0, 37.1]; // [west, south, east, north]

const SUBSTATION_COLOR = "#ffd166";
const GENERATION_COLOR = "#ef476f";

// Free MapLibre demo style — replace later with a self-hosted muted grey style.
const BASE_STYLE_URL = "https://demotiles.maplibre.org/style.json";

// ---------------------------------------------------------------------------

async function main() {
  const [voltageRegistry, meta] = await Promise.all([
    fetch(VOLTAGE_CLASSES_URL).then((r) => r.json()),
    fetch(META_URL)
      .then((r) => (r.ok ? r.json() : null))
      .catch(() => null),
  ]);

  const voltageClasses = voltageRegistry.classes;
  renderLegend(voltageClasses);
  renderMeta(meta);

  const map = new maplibregl.Map({
    container: "map",
    style: BASE_STYLE_URL,
    bounds: PK_BBOX,
    fitBoundsOptions: { padding: 20 },
    attributionControl: false,
  });
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-left");
  map.addControl(new maplibregl.ScaleControl({ maxWidth: 120, unit: "metric" }), "bottom-left");

  map.on("load", () => {
    for (const vc of voltageClasses) addVoltageLayer(map, vc);
    addSubstationsLayer(map);
    addGenerationLayer(map);
    wireLegendToggles(map, voltageClasses);
  });
}

// ---- layer setup ----------------------------------------------------------

function addVoltageLayer(map, vc) {
  const sourceId = `lines-${vc.id}`;
  const layerId = `lines-${vc.id}-layer`;

  map.addSource(sourceId, {
    type: "geojson",
    data: `data/${vc.geojson_filename}`,
    promoteId: "osm_id",
  });

  const paint = {
    "line-color": vc.color,
    "line-width": [
      "interpolate",
      ["linear"],
      ["zoom"],
      4, 0.6,
      8, 1.5,
      12, 3.0,
    ],
    "line-opacity": 0.9,
  };
  if (vc.line_dash) paint["line-dasharray"] = vc.line_dash;

  map.addLayer({
    id: layerId,
    type: "line",
    source: sourceId,
    minzoom: vc.min_zoom_visible,
    layout: { "line-cap": "round", "line-join": "round" },
    paint,
  });

  map.on("click", layerId, (e) => showLinePopup(map, vc, e));
  map.on("mouseenter", layerId, () => (map.getCanvas().style.cursor = "pointer"));
  map.on("mouseleave", layerId, () => (map.getCanvas().style.cursor = ""));
}

function addSubstationsLayer(map) {
  map.addSource("substations", { type: "geojson", data: "data/substations.geojson" });
  map.addLayer({
    id: "substations-layer",
    type: "circle",
    source: "substations",
    minzoom: 6,
    paint: {
      "circle-radius": ["interpolate", ["linear"], ["zoom"], 6, 2, 12, 6],
      "circle-color": SUBSTATION_COLOR,
      "circle-stroke-color": "#000",
      "circle-stroke-width": 0.6,
    },
  });
  map.on("click", "substations-layer", (e) => showPointPopup(e, "Substation"));
  map.on("mouseenter", "substations-layer", () => (map.getCanvas().style.cursor = "pointer"));
  map.on("mouseleave", "substations-layer", () => (map.getCanvas().style.cursor = ""));
}

function addGenerationLayer(map) {
  map.addSource("generation", { type: "geojson", data: "data/generation.geojson" });
  map.addLayer({
    id: "generation-layer",
    type: "circle",
    source: "generation",
    minzoom: 5,
    paint: {
      "circle-radius": ["interpolate", ["linear"], ["zoom"], 5, 3, 12, 8],
      "circle-color": GENERATION_COLOR,
      "circle-stroke-color": "#000",
      "circle-stroke-width": 0.6,
    },
  });
  map.on("click", "generation-layer", (e) => showPointPopup(e, "Generation plant"));
  map.on("mouseenter", "generation-layer", () => (map.getCanvas().style.cursor = "pointer"));
  map.on("mouseleave", "generation-layer", () => (map.getCanvas().style.cursor = ""));
}

// ---- legend / toggles -----------------------------------------------------

function renderLegend(voltageClasses) {
  const list = document.getElementById("voltage-list");
  list.innerHTML = voltageClasses
    .map(
      (vc) => `
      <li>
        <label>
          <input type="checkbox" data-voltage="${vc.id}" checked />
          <span class="swatch" style="color: ${vc.color}"></span>
          ${vc.label}
        </label>
      </li>`,
    )
    .join("");

  const legend = document.getElementById("legend");
  document.getElementById("legend-toggle").addEventListener("click", () => {
    legend.classList.toggle("open");
  });
}

function wireLegendToggles(map, voltageClasses) {
  for (const vc of voltageClasses) {
    const cb = document.querySelector(`input[data-voltage="${vc.id}"]`);
    cb.addEventListener("change", () => {
      map.setLayoutProperty(`lines-${vc.id}-layer`, "visibility", cb.checked ? "visible" : "none");
    });
  }

  for (const layer of ["substations", "generation"]) {
    const cb = document.querySelector(`input[data-layer="${layer}"]`);
    cb.addEventListener("change", () => {
      map.setLayoutProperty(`${layer}-layer`, "visibility", cb.checked ? "visible" : "none");
    });
  }
}

function renderMeta(meta) {
  const el = document.getElementById("meta-line");
  if (!meta || !meta.built_at) {
    el.textContent = "Data not yet built. Run `make refresh`.";
    return;
  }
  const builtAt = new Date(meta.built_at).toISOString().slice(0, 10);
  el.textContent = `Last refreshed: ${builtAt}`;
}

// ---- popups ---------------------------------------------------------------

function showLinePopup(map, vc, e) {
  const props = e.features[0].properties || {};
  const html = `
    <div class="popup-title">${escapeHtml(props.name || vc.label + " line")}</div>
    <div class="popup-row"><b>Voltage:</b> ${vc.label}</div>
    ${props.operator ? `<div class="popup-row"><b>Operator:</b> ${escapeHtml(props.operator)}</div>` : ""}
    ${props.osm_id ? `<div class="popup-row"><b>OSM way:</b>
      <a href="https://www.openstreetmap.org/way/${props.osm_id}" target="_blank" rel="noopener">${props.osm_id}</a></div>` : ""}
    <div class="popup-source">Source: ${escapeHtml(props.source || "osm")}</div>
  `;
  new maplibregl.Popup().setLngLat(e.lngLat).setHTML(html).addTo(map);
}

function showPointPopup(e, fallbackTitle) {
  const props = e.features[0].properties || {};
  const html = `
    <div class="popup-title">${escapeHtml(props.name || fallbackTitle)}</div>
    ${props.voltage ? `<div class="popup-row"><b>Voltage:</b> ${escapeHtml(props.voltage)} V</div>` : ""}
    ${props.operator ? `<div class="popup-row"><b>Operator:</b> ${escapeHtml(props.operator)}</div>` : ""}
    ${props.osm_id ? `<div class="popup-row"><b>OSM:</b>
      <a href="https://www.openstreetmap.org/${escapeHtml(props.osm_type || "node")}/${props.osm_id}" target="_blank" rel="noopener">${props.osm_id}</a></div>` : ""}
    <div class="popup-source">Source: ${escapeHtml(props.source || "osm")}</div>
  `;
  new maplibregl.Popup().setLngLat(e.lngLat).setHTML(html).addTo(e.target);
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

main().catch((err) => {
  console.error(err);
  document.getElementById("meta-line").textContent = "Failed to load. See console.";
});
