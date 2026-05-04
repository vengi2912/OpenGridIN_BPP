"""Overpass API queries for Pakistan transmission infrastructure.

We query one voltage class at a time so a slow/timed-out query doesn't poison
the whole refresh. Results are cached on disk under pipeline/.cache/ so reruns
during development are fast.

Overpass endpoints rotate; if the primary times out we fall back to mirrors.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass

import requests

from pipeline._paths import PIPELINE_CACHE
from pipeline.voltage_classes import VoltageClass

OVERPASS_ENDPOINTS: tuple[str, ...] = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.fr/api/interpreter",
)

REQUEST_TIMEOUT_S = 300
RETRY_BACKOFF_S = (5, 15, 45)


@dataclass(frozen=True)
class OverpassResult:
    voltage_class_id: str
    raw: dict
    fetched_at: str  # ISO 8601


def query_lines_for_voltage(vc: VoltageClass) -> OverpassResult:
    """Fetch all `power=line` and `power=cable` ways in PK matching this voltage class.

    HVDC is identified by frequency=0 (DC). All other classes match the exact
    voltage value (or that value within a semicolon-separated list).
    """
    if vc.is_hvdc:
        body = _hvdc_query()
    else:
        body = _ac_voltage_query(vc.voltage_v)
    return _fetch_or_cache(f"lines_{vc.id}", body, vc.id)


def query_substations_pk() -> OverpassResult:
    """Fetch all `power=substation` features in Pakistan."""
    body = _substations_query()
    return _fetch_or_cache("substations", body, "substations")


def query_generation_pk() -> OverpassResult:
    """Fetch all `power=plant` features in Pakistan."""
    body = _generation_query()
    return _fetch_or_cache("generation", body, "generation")


def _ac_voltage_query(voltage_v: int) -> str:
    return f"""
    [out:json][timeout:{REQUEST_TIMEOUT_S - 30}];
    area["ISO3166-1"="PK"][admin_level=2]->.pk;
    (
      way(area.pk)["power"="line"]["voltage"~"(^|;){voltage_v}(;|$)"];
      way(area.pk)["power"="cable"]["voltage"~"(^|;){voltage_v}(;|$)"];
    );
    out geom tags;
    """.strip()


def _hvdc_query() -> str:
    return f"""
    [out:json][timeout:{REQUEST_TIMEOUT_S - 30}];
    area["ISO3166-1"="PK"][admin_level=2]->.pk;
    (
      way(area.pk)["power"="line"]["frequency"="0"];
      way(area.pk)["power"="cable"]["frequency"="0"];
    );
    out geom tags;
    """.strip()


def _substations_query() -> str:
    return f"""
    [out:json][timeout:{REQUEST_TIMEOUT_S - 30}];
    area["ISO3166-1"="PK"][admin_level=2]->.pk;
    (
      node(area.pk)["power"="substation"];
      way(area.pk)["power"="substation"];
      relation(area.pk)["power"="substation"];
    );
    out center tags;
    """.strip()


def _generation_query() -> str:
    return f"""
    [out:json][timeout:{REQUEST_TIMEOUT_S - 30}];
    area["ISO3166-1"="PK"][admin_level=2]->.pk;
    (
      node(area.pk)["power"="plant"];
      way(area.pk)["power"="plant"];
      relation(area.pk)["power"="plant"];
    );
    out center tags;
    """.strip()


def _fetch_or_cache(cache_key: str, body: str, label: str) -> OverpassResult:
    PIPELINE_CACHE.mkdir(parents=True, exist_ok=True)
    body_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()[:12]
    cache_file = PIPELINE_CACHE / f"{cache_key}.{body_hash}.json"

    if cache_file.exists():
        cached = json.loads(cache_file.read_text(encoding="utf-8"))
        return OverpassResult(label, cached["raw"], cached["fetched_at"])

    raw = _post_with_failover(body)
    fetched_at = _utc_now_iso()
    cache_file.write_text(
        json.dumps({"fetched_at": fetched_at, "raw": raw}),
        encoding="utf-8",
    )
    return OverpassResult(label, raw, fetched_at)


def _post_with_failover(body: str) -> dict:
    last_err: Exception | None = None
    for endpoint in OVERPASS_ENDPOINTS:
        for backoff in RETRY_BACKOFF_S:
            try:
                resp = requests.post(
                    endpoint,
                    data={"data": body},
                    timeout=REQUEST_TIMEOUT_S,
                    headers={"User-Agent": "OpenGridPK/0.1 (https://github.com/opengridpk)"},
                )
                resp.raise_for_status()
                return resp.json()
            except requests.RequestException as e:
                last_err = e
                time.sleep(backoff)
    raise RuntimeError(f"All Overpass endpoints failed; last error: {last_err}")


def _utc_now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
