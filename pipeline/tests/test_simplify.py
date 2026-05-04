"""Tests for geometry simplification + length calculation."""

from pipeline.simplify import line_length_km, simplify_line_features


def _line(coords: list[list[float]]) -> dict:
    return {
        "type": "Feature",
        "geometry": {"type": "LineString", "coordinates": coords},
        "properties": {},
    }


def test_simplify_keeps_shape_collinear_points_dropped():
    # Three collinear points -> should be reduced to two endpoints.
    f = _line([[70.0, 30.0], [70.5, 30.5], [71.0, 31.0]])
    [out] = simplify_line_features([f], tolerance_deg=0.01)
    assert len(out["geometry"]["coordinates"]) == 2


def test_length_haversine_known_distance():
    # 1 degree of latitude is ~111 km.
    f = _line([[70.0, 30.0], [70.0, 31.0]])
    km = line_length_km([f])
    assert 110 < km < 112
