"""Repository path constants. Single source of truth for where things live."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

PIPELINE_DIR = REPO_ROOT / "pipeline"
PIPELINE_CACHE = PIPELINE_DIR / ".cache"

DATA_DIR = REPO_ROOT / "data"
OVERRIDES_DIR = DATA_DIR / "overrides"
REFERENCE_DIR = DATA_DIR / "reference"
VOLTAGE_CLASSES_FILE = REFERENCE_DIR / "voltage_classes.json"

SITE_DIR = REPO_ROOT / "docs"
SITE_DATA_DIR = SITE_DIR / "data"
SITE_META_FILE = SITE_DATA_DIR / "meta.json"
