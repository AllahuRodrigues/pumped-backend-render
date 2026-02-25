from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.engine import Connection

from db.session import get_db


router = APIRouter(prefix="/api/events", tags=["events"])


class EventIn(BaseModel):
    name: str
    userId: str
    testId: Optional[str] = None
    variant: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None


@router.post("")
def log_event(payload: EventIn, db: Connection = Depends(get_db)) -> Dict[str, Any]:
    event_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    db.execute(
        text(
            """
            INSERT INTO events (id, event_name, user_id, test_id, variant, properties_json, created_at)
            VALUES (:id, :event_name, :user_id, :test_id, :variant, :properties_json, :created_at);
            """
        ),
        {
            "id": event_id,
            "event_name": payload.name,
            "user_id": payload.userId,
            "test_id": payload.testId,
            "variant": payload.variant,
            "properties_json": json.dumps(payload.properties) if payload.properties is not None else None,
            "created_at": now,
        },
    )

    return {"status": "ok", "id": event_id}

