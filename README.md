# OpenGridPK

> Pakistan's transmission grid, on one map.

An open, interactive map of every 66 kV, 132 kV, 220 kV, 500 kV, 765 kV, and ±660 kV HVDC transmission line in Pakistan. Built from OpenStreetMap and PyPSA-Earth data, served as a static site for free.

**Status:** v0 — scaffolding in progress.

## What this is

- A free, public-facing reference map of Pakistan's high-voltage grid
- A reusable, downloadable GeoJSON dataset of the network (lines, substations, generation plants)
- An automatically refreshed snapshot — the build pipeline reruns monthly and pushes updates to the live site

## What this is not

- Not a SCADA / live operations tool. There is no real-time line loading, status, or alarms.
- Not authoritative — the data comes from open sources and is provided as-is. Always cross-check with NTDC / DISCO records for engineering decisions.

## How it works

```
Overpass API ──┐
               ├──► merge ──► validate ──► simplify ──► site/data/*.geojson
PyPSA-Earth ───┘                                            │
                                                            ▼
data/overrides/  ────────────────────► overlay         MapLibre GL JS
                                                       (static GitHub Pages site)
```

Two cleanly separated halves:

1. **Build pipeline** (Python in `pipeline/`) — fetches OSM data via Overpass, extracts the Pakistan subset from PyPSA-Earth, merges with hand-curated corrections in `data/overrides/`, validates, simplifies, and writes GeoJSON files to `site/data/`.
2. **Static site** (HTML / JS in `site/`) — MapLibre GL JS loads the pre-baked GeoJSON and renders styled vector layers. No backend.

The build pipeline runs monthly via GitHub Actions and commits refreshed data back to `main`, which GitHub Pages auto-deploys.

## Run locally

> _Coming soon — pipeline is being scaffolded._

```bash
# fetch & rebuild data
cd pipeline
uv sync
make refresh

# serve the static site locally
make serve   # → http://localhost:8000
```

## Contributing data corrections

OSM coverage of Pakistan's 132 kV and 66 kV networks is incomplete. If you spot a missing line, a wrong voltage, or an incorrect name:

1. **Best:** fix it in OpenStreetMap directly (everyone benefits).
2. **Faster:** add an entry to `data/overrides/` (see `data/overrides/README.md`) and open a PR. Your correction is merged on top of the OSM data during build.

Each line on the map carries provenance: the popup shows whether the data came from OSM, PyPSA-Earth, or a local override.

## Data sources & attribution

- **OpenStreetMap contributors** — line geometries via the Overpass API. Licensed under [ODbL](https://www.openstreetmap.org/copyright).
- **PyPSA-Earth** — processed, voltage-validated grid topology. Licensed under MIT. <https://pypsa-earth.readthedocs.io/>
- Inspiration: [OpenInfraMap](https://openinframap.org/), [OpenGridWorks](https://opengridworks.com/).

## License

- **Code:** MIT (see [LICENSE](LICENSE)).
- **Derived data** in `site/data/`: ODbL, inherited from OpenStreetMap.
