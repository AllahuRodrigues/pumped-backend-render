from __future__ import annotations

import json
from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from core.firestore_client import get_firestore


router = APIRouter(prefix="/api/experiments", tags=["experiments"])


def _tests_json_path() -> Path:
    override = os.getenv("TESTS_JSON_PATH")
    if override:
        return Path(override)
    here = Path(__file__).resolve()
    return here.parents[2] / "config" / "tests.json"


def _load_tests() -> Dict[str, Any]:
    path = _tests_json_path()
    if not path.exists():
        return {"tests": []}
    return json.loads(path.read_text())


@router.get("/tests")
async def list_tests() -> Dict[str, Any]:
    payload = _load_tests()
    tests: List[Dict[str, Any]] = payload.get("tests", [])
    active = [t for t in tests if t.get("isActive") is True]
    return {
        "count": len(active),
        "tests": active,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/results/{test_id}")
async def results(test_id: str) -> Dict[str, Any]:
    availability = get_firestore()
    if availability.client is None:
        raise HTTPException(status_code=503, detail=availability.reason or "firestore unavailable")

    db = availability.client

    exposures = (
        db.collection("analytics_events")
        .where("eventName", "==", "experiment_exposure")
        .where("experimentId", "==", test_id)
        .stream()
    )

    exposure_by_variant: Dict[str, int] = {}
    for doc in exposures:
        data = doc.to_dict() or {}
        variant = data.get("variant") or data.get("treatment") or "unknown"
        exposure_by_variant[variant] = exposure_by_variant.get(variant, 0) + 1

    conversions = (
        db.collection("analytics_events")
        .where("eventName", "==", "experiment_conversion")
        .where("experimentId", "==", test_id)
        .stream()
    )

    conversion_by_variant: Dict[str, int] = {}
    for doc in conversions:
        data = doc.to_dict() or {}
        variant = data.get("variant") or "unknown"
        conversion_by_variant[variant] = conversion_by_variant.get(variant, 0) + 1

    results_payload: Dict[str, Any] = {}
    for variant, exposures_count in exposure_by_variant.items():
        conv = conversion_by_variant.get(variant, 0)
        rate = (conv / exposures_count) if exposures_count else 0.0
        results_payload[variant] = {
            "exposures": exposures_count,
            "conversions": conv,
            "conversionRate": round(rate, 4),
        }

    return {"testId": test_id, "results": results_payload, "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok", "service": "experiments"}

