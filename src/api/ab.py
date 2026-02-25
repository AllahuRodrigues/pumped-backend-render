from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.engine import Connection

from db.session import get_db


router = APIRouter(prefix="/api/ab", tags=["ab"])


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


def _stable_bucket(test_id: str, user_id: str) -> float:
    raw = f"{test_id}:{user_id}".encode("utf-8")
    h = hashlib.sha256(raw).hexdigest()
    top32 = int(h[:8], 16)
    return top32 / 0xFFFFFFFF


def _choose_variant(test: Dict[str, Any], user_id: str) -> str:
    test_id = str(test.get("id") or "")
    variants: List[str] = list(test.get("variants") or [])
    if not test_id or not variants:
        return str(test.get("defaultVariant") or "control")

    weights: Dict[str, float] = dict(test.get("weights") or {})
    default_variant = str(test.get("defaultVariant") or variants[0])

    total = 0.0
    for v in variants:
        w = float(weights.get(v, 0.0))
        if w > 0:
            total += w

    if total <= 0:
        return default_variant

    bucket = _stable_bucket(test_id, user_id)
    cumulative = 0.0
    for v in variants:
        w = float(weights.get(v, 0.0))
        if w <= 0:
            continue
        cumulative += w / total
        if bucket <= cumulative:
            return v

    return default_variant


def _get_active_test(test_id: str) -> Dict[str, Any]:
    payload = _load_tests()
    tests: List[Dict[str, Any]] = payload.get("tests", [])
    for t in tests:
        if t.get("id") == test_id:
            if t.get("isActive") is True:
                return t
            raise HTTPException(status_code=404, detail="test is not active")
    raise HTTPException(status_code=404, detail="unknown test id")


class ExposureIn(BaseModel):
    testId: str
    userId: str
    variant: Optional[str] = None


@router.get("/tests")
def list_tests() -> Dict[str, Any]:
    payload = _load_tests()
    tests: List[Dict[str, Any]] = payload.get("tests", [])
    active = [t for t in tests if t.get("isActive") is True]
    return {
        "count": len(active),
        "tests": active,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/variant/{test_id}")
def variant(test_id: str, userId: str) -> Dict[str, Any]:
    t = _get_active_test(test_id)
    v = _choose_variant(t, userId)
    return {
        "testId": test_id,
        "userId": userId,
        "variant": v,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/exposure")
def log_exposure(payload: ExposureIn, db: Connection = Depends(get_db)) -> Dict[str, Any]:
    t = _get_active_test(payload.testId)
    v = payload.variant or _choose_variant(t, payload.userId)

    now = datetime.now(timezone.utc).isoformat()
    db.execute(
        text(
            """
            INSERT INTO ab_exposures (test_id, user_id, variant, exposed_at)
            VALUES (:test_id, :user_id, :variant, :exposed_at)
            ON CONFLICT (test_id, user_id) DO UPDATE SET
              variant = excluded.variant,
              exposed_at = excluded.exposed_at;
            """
        ),
        {"test_id": payload.testId, "user_id": payload.userId, "variant": v, "exposed_at": now},
    )

    return {"status": "ok", "testId": payload.testId, "userId": payload.userId, "variant": v}


@router.get("/results/{test_id}")
def results(test_id: str, conversionEvent: str = "conversion", db: Connection = Depends(get_db)) -> Dict[str, Any]:
    _get_active_test(test_id)

    exposures_rows = db.execute(
        text(
            """
            SELECT variant, COUNT(*) AS exposures
            FROM ab_exposures
            WHERE test_id = :test_id
            GROUP BY variant;
            """
        ),
        {"test_id": test_id},
    ).fetchall()

    conversions_rows = db.execute(
        text(
            """
            SELECT COALESCE(e.variant, 'unknown') AS variant, COUNT(DISTINCT ev.user_id) AS conversions
            FROM events ev
            LEFT JOIN ab_exposures e
              ON e.test_id = ev.test_id AND e.user_id = ev.user_id
            WHERE ev.test_id = :test_id AND ev.event_name = :event_name
            GROUP BY COALESCE(e.variant, 'unknown');
            """
        ),
        {"test_id": test_id, "event_name": conversionEvent},
    ).fetchall()

    exposure_by_variant = {row[0]: int(row[1]) for row in exposures_rows}
    conversion_by_variant = {row[0]: int(row[1]) for row in conversions_rows}

    variants = set(exposure_by_variant.keys()) | set(conversion_by_variant.keys())
    out: Dict[str, Any] = {}
    for v in sorted(variants):
        exp = exposure_by_variant.get(v, 0)
        conv = conversion_by_variant.get(v, 0)
        out[v] = {
            "exposures": exp,
            "conversions": conv,
            "conversionRate": round((conv / exp), 4) if exp else 0.0,
        }

    return {"testId": test_id, "conversionEvent": conversionEvent, "results": out}

