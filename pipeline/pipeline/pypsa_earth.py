"""PyPSA-Earth integration: extract the Pakistan subset as a topology baseline.

Strategy: use a pinned snapshot of pypsa-earth, run its data-extraction stage
restricted to PK, then read the resulting NetCDF and convert lines + buses to
GeoJSON. PyPSA-Earth's processed output has voltages validated and topology
snapped, so we treat it as the topology baseline; OSM enriches with names/owners.

This module is a stub. PyPSA-Earth integration has setup overhead (cloning the
repo, installing its full dependency tree, running snakemake). For the first
build we may run this once locally and commit the cached output to
`pipeline/.cache/pypsa_earth/` rather than rerun every CI build.
"""

from __future__ import annotations

from dataclasses import dataclass, field

PINNED_PYPSA_EARTH_SHA = "TBD"  # pin during first integration


@dataclass(frozen=True)
class PyPSAEarthSnapshot:
    """Lines and buses extracted from PyPSA-Earth for Pakistan."""

    lines: list[dict] = field(default_factory=list)  # GeoJSON Features (LineString)
    buses: list[dict] = field(default_factory=list)  # GeoJSON Features (Point)
    source_sha: str = PINNED_PYPSA_EARTH_SHA


def load_pakistan_subset() -> PyPSAEarthSnapshot:
    """Return the Pakistan subset as GeoJSON-shaped features.

    First implementation will:
      1. Check pipeline/.cache/pypsa_earth/{sha}/ for a prior export.
      2. If absent, clone pypsa-earth at PINNED_PYPSA_EARTH_SHA, run the
         country-restricted extraction, convert NetCDF -> GeoJSON, cache.
      3. Return the cached snapshot.

    Until implementation, returns an empty snapshot so the rest of the pipeline
    can develop end-to-end against OSM only.
    """
    return PyPSAEarthSnapshot()
