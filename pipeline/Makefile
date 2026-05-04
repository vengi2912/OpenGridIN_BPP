# OpenGridPK build pipeline
#
# Common targets:
#   make refresh   - Full rebuild: Overpass + PyPSA-Earth -> site/data/*.geojson
#   make serve     - Serve the static site at http://localhost:8000
#   make test      - Run pytest
#   make lint      - Run ruff
#   make clean     - Remove pipeline working/cache dirs

PYTHON ?= python
SITE_DIR := ../site
DATA_OUT := $(SITE_DIR)/data
VENV := .venv
VENV_PY := $(VENV)/Scripts/python.exe

.PHONY: help install refresh serve test lint clean

help:
	@echo "Targets:"
	@echo "  install   Create .venv and install pipeline deps (one time)"
	@echo "  refresh   Full rebuild of $(DATA_OUT)/*.geojson"
	@echo "  serve     Serve $(SITE_DIR) on http://localhost:8000"
	@echo "  test      Run pytest"
	@echo "  lint      Run ruff"
	@echo "  clean     Remove cache/temp directories"

install:
	$(PYTHON) -m venv $(VENV)
	$(VENV_PY) -m pip install --upgrade pip
	$(VENV_PY) -m pip install -e ".[dev]"

refresh:
	$(VENV_PY) -m pipeline.refresh

serve:
	cd $(SITE_DIR) && $(PYTHON) -m http.server 8000

test:
	$(VENV_PY) -m pytest

lint:
	$(VENV_PY) -m ruff check .

clean:
	rm -rf .cache output_raw pypsa-earth-clone __pycache__ .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
