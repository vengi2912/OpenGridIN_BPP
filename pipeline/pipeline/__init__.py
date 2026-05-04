"""OpenGridPK build pipeline.

Pulls Pakistan transmission grid data from OpenStreetMap (Overpass) and
PyPSA-Earth, merges with local overrides, validates, simplifies, and exports
GeoJSON files consumed by the static MapLibre site.
"""

__version__ = "0.1.0"
