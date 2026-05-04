# Data Overrides

This folder lets you fix OSM data without waiting for the OSM upstream edit cycle. Anything here is merged on top of the OSM + PyPSA-Earth data during the build pipeline (see `pipeline/pipeline/merge.py`).

> **Prefer fixing OSM upstream when possible.** Edits to OSM benefit every consumer of the data, not just OpenGridPK. Use overrides when an OSM edit is impractical (you don't have ground truth for all attributes, the change is contested, etc.).

## File types

### `voltage_corrections.json`

Map an OSM way ID to its corrected voltage in volts. The pipeline will move that line to the correct voltage layer.

```json
{
  "$schema_comment": "{ osm_way_id (string): voltage_in_volts (number) }",
  "comment_example": "// 'OSM tagged 132 kV but it's actually 220 kV by the substation portal':",
  "123456789": 220000
}
```

### `name_corrections.json`

Map an OSM way ID to its canonical English name. Useful when OSM has the line in Urdu only or with an inconsistent name.

```json
{
  "$schema_comment": "{ osm_way_id (string): canonical_name (string) }",
  "987654321": "Guddu – Multan 500 kV (Circuit 1)"
}
```

### `add_lines.geojson`

Standard GeoJSON FeatureCollection of LineStrings. Use this for lines that are entirely missing from OSM (common at 66 kV).

Each feature MUST have these properties:

| Property | Type | Required | Notes |
|---|---|---|---|
| `voltage` | number | yes | In volts (e.g., 132000) |
| `name` | string | yes | Canonical line name |
| `is_hvdc` | bool | no | Default false |
| `owner` | string | no | E.g., "NTDC", "LESCO", "K-Electric" |
| `source_note` | string | yes | Where you got the route (e.g., "NTDC SLD 2023, page 14, hand-traced") |

Example:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "voltage": 132000,
        "name": "Sample 132 kV Line",
        "owner": "MEPCO",
        "source_note": "MEPCO SLD 2024, hand-traced approximate route"
      },
      "geometry": {
        "type": "LineString",
        "coordinates": [[71.5, 30.2], [71.6, 30.3]]
      }
    }
  ]
}
```

## Provenance

Every overridden or added feature is tagged in the final output with `properties.source = "override"` so users see in the popup that this line came from a local correction, not OSM.

## Pull request etiquette

When opening a PR with a correction:
- Cite the source (NTDC document name + page, photograph, observed installation, etc.) in `source_note`
- One PR per logical correction (don't bundle 50 unrelated edits)
- Re-run `make refresh && make test` locally before pushing
