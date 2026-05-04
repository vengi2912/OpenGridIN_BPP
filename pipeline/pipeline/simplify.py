"""Geometry simplification to keep web payload small.

We use Douglas-Peucker via Shapely. Tolerance is in degrees because input is
WGS84; ~50 m at PK latitudes is roughly 0.0005°. Tested empirically:
- 0.0005 keeps the visual shape sharp at z=10
- 0.001 (~100 m) is fine when zoom < 8 but starts visibly cutting corners on
  curved rights-of-way.
"""

from __future__ import annotations

from shapely.geometry import LineString, mapping, shape

DEFAULT_TOLERANCE_DEG = 0.0005  # ~50 m


def simplify_line_features(
    features: list[dict],
    tolerance_deg: float = DEFAULT_TOLERANCE_DEG,
) -> list[dict]:
    out: list[dict] = []
    for f in features:
        geom = shape(f["geometry"])
        if not isinstance(geom, LineString):
            out.append(f)
            continue
        simplified = geom.simplify(tolerance_deg, preserve_topology=False)
        if simplified.is_empty or len(simplified.coords) < 2:
            # Simplification collapsed it; keep the original.
            out.append(f)
            continue
        new_f = dict(f)
        new_f["geometry"] = mapping(simplified)
        out.append(new_f)
    return out


def line_length_km(features: list[dict]) -> float:
    """Approximate haversine total length over a list of LineString features.

    Uses Shapely's geographic distance approximation; good enough for the
    regression-check tolerance (±20 %).
    """
    from math import asin, cos, radians, sin, sqrt

    EARTH_R_KM = 6371.0
    total = 0.0
    for f in features:
        coords = f["geometry"]["coordinates"]
        for (lon1, lat1), (lon2, lat2) in zip(coords[:-1], coords[1:]):
            phi1, phi2 = radians(lat1), radians(lat2)
            dphi = radians(lat2 - lat1)
            dlam = radians(lon2 - lon1)
            a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlam / 2) ** 2
            total += 2 * EARTH_R_KM * asin(sqrt(a))
    return total
