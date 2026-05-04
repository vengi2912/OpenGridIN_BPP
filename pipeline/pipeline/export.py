"""Write final GeoJSON files to site/data/ and update meta.json.

Also copies data/reference/voltage_classes.json into site/data/ so the static
site is self-contained (the same file is the canonical source for the Python
pipeline AND the JS app).
"""

from __future__ import annotations

import json
import shutil
from typing import Any

from pipeline._paths import SITE_DATA_DIR, SITE_META_FILE, VOLTAGE_CLASSES_FILE


def write_feature_collection(filename: str, features: list[dict]) -> None:
    SITE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    fc = {"type": "FeatureCollection", "features": features}
    path = SITE_DATA_DIR / filename
    path.write_text(json.dumps(fc, separators=(",", ":")), encoding="utf-8")


def write_meta(meta: dict[str, Any]) -> None:
    SITE_META_FILE.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def copy_reference_files() -> None:
    """Copy data/reference/* into site/data/ so the site can fetch them directly."""
    SITE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(VOLTAGE_CLASSES_FILE, SITE_DATA_DIR / "voltage_classes.json")
