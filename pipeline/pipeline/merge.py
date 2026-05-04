"""Merge OSM Overpass output, PyPSA-Earth snapshot, and local overrides.

Output features carry provenance via `properties.source` (osm | pypsa-earth |
override) so the static site's click popup can attribute correctly.

Order of precedence (later wins):
  1. PyPSA-Earth processed lines (clean topology baseline)
  2. Raw OSM lines not represented in PyPSA-Earth (matched by OSM way ID)
  3. data/overrides/voltage_corrections.json
  4. data/overrides/name_corrections.json
  5. data/overrides/add_lines.geojson (entirely manual additions)
"""

from __future__ import annotations

import json
from typing import Any

from pipeline._paths import OVERRIDES_DIR
from pipeline.overpass import OverpassResult
from pipeline.pypsa_earth import PyPSAEarthSnapshot
from pipeline.voltage_classes import VoltageClass


def merge_lines(
    voltage_class: VoltageClass,
    osm_result: OverpassResult,
    pypsa: PyPSAEarthSnapshot,
) -> list[dict]:
    """Return a list of GeoJSON LineString features for one voltage class."""
    osm_features = _osm_to_geojson_lines(osm_result, voltage_class)
    pypsa_features = _filter_pypsa_for_class(pypsa, voltage_class)
    base = _combine_with_pypsa_priority(pypsa_features, osm_features)
    base = _apply_voltage_corrections(base, voltage_class)
    base = _apply_name_corrections(base)
    base.extend(_load_added_lines(voltage_class))
    return base


def merge_substations(osm_result: OverpassResult) -> list[dict]:
    """Return GeoJSON Point features for transmission-level substations in PK."""
    return _osm_to_geojson_points(osm_result, kind="substation")


def merge_generation(osm_result: OverpassResult) -> list[dict]:
    """Return GeoJSON Point features for generation plants in PK."""
    return _osm_to_geojson_points(osm_result, kind="generation")


# --- internals -------------------------------------------------------------


def _osm_to_geojson_lines(result: OverpassResult, vc: VoltageClass) -> list[dict]:
    """Convert Overpass JSON `way` elements to GeoJSON LineString features."""
    elements = result.raw.get("elements", [])
    features: list[dict] = []
    for el in elements:
        if el.get("type") != "way" or "geometry" not in el:
            continue
        coords = [[pt["lon"], pt["lat"]] for pt in el["geometry"]]
        if len(coords) < 2:
            continue
        tags = el.get("tags", {})
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": coords},
                "properties": {
                    "source": "osm",
                    "osm_id": el["id"],
                    "voltage": vc.voltage_v,
                    "is_hvdc": vc.is_hvdc,
                    "name": tags.get("name"),
                    "operator": tags.get("operator"),
                    "tags_raw": tags,
                },
            }
        )
    return features


def _osm_to_geojson_points(result: OverpassResult, kind: str) -> list[dict]:
    elements = result.raw.get("elements", [])
    features: list[dict] = []
    for el in elements:
        lon, lat = _extract_point(el)
        if lon is None:
            continue
        tags = el.get("tags", {})
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {
                    "source": "osm",
                    "osm_id": el["id"],
                    "osm_type": el["type"],
                    "kind": kind,
                    "name": tags.get("name"),
                    "voltage": tags.get("voltage"),
                    "operator": tags.get("operator"),
                    "tags_raw": tags,
                },
            }
        )
    return features


def _extract_point(el: dict) -> tuple[float | None, float | None]:
    if el.get("type") == "node":
        return el.get("lon"), el.get("lat")
    center = el.get("center")
    if center:
        return center.get("lon"), center.get("lat")
    return None, None


def _filter_pypsa_for_class(pypsa: PyPSAEarthSnapshot, vc: VoltageClass) -> list[dict]:
    out: list[dict] = []
    for f in pypsa.lines:
        if int(f["properties"].get("voltage", 0)) == vc.voltage_v:
            out.append(_with_source(f, "pypsa-earth"))
    return out


def _combine_with_pypsa_priority(
    pypsa_features: list[dict],
    osm_features: list[dict],
) -> list[dict]:
    """PyPSA-Earth features win when they share an osm_id with raw OSM."""
    pypsa_osm_ids = {f["properties"].get("osm_id") for f in pypsa_features}
    pypsa_osm_ids.discard(None)
    surviving_osm = [f for f in osm_features if f["properties"].get("osm_id") not in pypsa_osm_ids]
    return [*pypsa_features, *surviving_osm]


def _apply_voltage_corrections(features: list[dict], vc: VoltageClass) -> list[dict]:
    path = OVERRIDES_DIR / "voltage_corrections.json"
    if not path.exists():
        return features
    raw = json.loads(path.read_text(encoding="utf-8"))
    corrections: dict[str, int] = {k: int(v) for k, v in raw.items() if not k.startswith("$")}
    if not corrections:
        return features

    out: list[dict] = []
    for f in features:
        osm_id = str(f["properties"].get("osm_id", ""))
        corrected_v = corrections.get(osm_id)
        if corrected_v is None:
            out.append(f)
            continue
        if corrected_v == vc.voltage_v:
            f = _with_source(f, "override")
            f["properties"]["voltage"] = corrected_v
            out.append(f)
        # else: this feature belongs to a DIFFERENT voltage class now,
        # so we drop it from this layer. It will appear in that other layer
        # because that layer's _apply_voltage_corrections will pick it up.
    return out


def _apply_name_corrections(features: list[dict]) -> list[dict]:
    path = OVERRIDES_DIR / "name_corrections.json"
    if not path.exists():
        return features
    raw = json.loads(path.read_text(encoding="utf-8"))
    name_map: dict[str, str] = {k: v for k, v in raw.items() if not k.startswith("$")}
    if not name_map:
        return features
    for f in features:
        osm_id = str(f["properties"].get("osm_id", ""))
        new_name = name_map.get(osm_id)
        if new_name is not None:
            f["properties"]["name"] = new_name
            f["properties"]["source"] = "override"
    return features


def _load_added_lines(vc: VoltageClass) -> list[dict]:
    path = OVERRIDES_DIR / "add_lines.geojson"
    if not path.exists():
        return []
    fc = json.loads(path.read_text(encoding="utf-8"))
    out: list[dict] = []
    for f in fc.get("features", []):
        props = f.get("properties", {})
        v = int(props.get("voltage", 0))
        if v != vc.voltage_v:
            continue
        f = dict(f)
        f["properties"] = {**props, "source": "override", "is_hvdc": vc.is_hvdc}
        out.append(f)
    return out


def _with_source(feature: dict, source: str) -> dict:
    f = dict(feature)
    f["properties"] = {**feature.get("properties", {}), "source": source}
    return f


# Type alias just for readability when this file is imported elsewhere.
GeoJSONFeature = dict[str, Any]
