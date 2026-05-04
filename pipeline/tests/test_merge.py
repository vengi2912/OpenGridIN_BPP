"""Tests for the merge logic, focused on override application + provenance."""

from pipeline.merge import merge_lines
from pipeline.overpass import OverpassResult
from pipeline.pypsa_earth import PyPSAEarthSnapshot
from pipeline.voltage_classes import by_id


def _osm_way(way_id: int, voltage: int, name: str = "Test") -> dict:
    return {
        "type": "way",
        "id": way_id,
        "geometry": [{"lon": 70.0, "lat": 30.0}, {"lon": 71.0, "lat": 31.0}],
        "tags": {"power": "line", "voltage": str(voltage), "name": name},
    }


def test_osm_only_features_get_osm_provenance():
    vc = by_id("220kv")
    osm = OverpassResult("220kv", {"elements": [_osm_way(111, 220000)]}, "2026-05-04T00:00:00Z")
    out = merge_lines(vc, osm, PyPSAEarthSnapshot())
    assert len(out) == 1
    assert out[0]["properties"]["source"] == "osm"
    assert out[0]["properties"]["osm_id"] == 111
    assert out[0]["properties"]["voltage"] == 220000


def test_lines_under_two_points_are_dropped():
    vc = by_id("220kv")
    bad = {
        "type": "way",
        "id": 222,
        "geometry": [{"lon": 70.0, "lat": 30.0}],
        "tags": {"power": "line", "voltage": "220000"},
    }
    osm = OverpassResult("220kv", {"elements": [bad]}, "2026-05-04T00:00:00Z")
    out = merge_lines(vc, osm, PyPSAEarthSnapshot())
    assert out == []
