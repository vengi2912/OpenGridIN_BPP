"""Build-blocking sanity checks. Fail loud if any of these trip.

The aim is to catch silent breakage: an Overpass mirror returned an empty
response, an override file is malformed, geometry got mangled, etc.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from shapely.geometry import shape

from pipeline._paths import SITE_META_FILE
from pipeline.voltage_classes import VoltageClass

LENGTH_DELTA_TOLERANCE = 0.20  # ±20 % vs previous run
COUNT_DELTA_TOLERANCE = 0.20


@dataclass
class ValidationFailure(Exception):
    message: str

    def __str__(self) -> str:
        return self.message


def validate_lines(features: list[dict], vc: VoltageClass) -> None:
    if not features:
        # A class might genuinely have zero lines (e.g., 765 kV not yet built),
        # so this is a warning case handled by the regression check below, not
        # a hard fail here.
        return

    for f in features:
        v = f["properties"].get("voltage")
        if int(v) != vc.voltage_v:
            raise ValidationFailure(
                f"{vc.id}: feature osm_id={f['properties'].get('osm_id')} "
                f"has voltage={v}, expected {vc.voltage_v}"
            )
        geom = shape(f["geometry"])
        if not geom.is_valid:
            raise ValidationFailure(
                f"{vc.id}: invalid geometry for osm_id={f['properties'].get('osm_id')}"
            )
        coords = f["geometry"]["coordinates"]
        if len(coords) < 2:
            raise ValidationFailure(
                f"{vc.id}: line has <2 points osm_id={f['properties'].get('osm_id')}"
            )


def regression_check(
    current_lengths_km: dict[str, float],
    current_counts: dict[str, int],
) -> list[str]:
    """Compare new totals against previous build's meta.json. Returns warnings.

    A drop > 20 % per class is suspicious (likely an Overpass hiccup or a
    map-stylist mistake). We return warnings rather than hard-fail so the build
    can still publish if the operator confirms it; CI workflow can decide.
    """
    if not SITE_META_FILE.exists():
        return []
    prev = json.loads(SITE_META_FILE.read_text(encoding="utf-8"))
    warnings: list[str] = []
    for cid, new_km in current_lengths_km.items():
        old_km = prev.get("line_lengths_km", {}).get(cid)
        if old_km and abs(new_km - old_km) / old_km > LENGTH_DELTA_TOLERANCE:
            warnings.append(
                f"{cid}: total length changed by >{LENGTH_DELTA_TOLERANCE:.0%} "
                f"({old_km:.0f} -> {new_km:.0f} km)"
            )
    for cid, new_n in current_counts.items():
        old_n = prev.get("line_counts", {}).get(cid)
        if old_n and abs(new_n - old_n) / old_n > COUNT_DELTA_TOLERANCE:
            warnings.append(
                f"{cid}: line count changed by >{COUNT_DELTA_TOLERANCE:.0%} "
                f"({old_n} -> {new_n})"
            )
    return warnings
