from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.firestore_client import get_firestore


router = APIRouter(prefix="/api/gyms", tags=["gyms"])


class JoinBody(BaseModel):
    userId: str


@router.post("/{gym_id}/join")
async def join_gym(gym_id: str, body: JoinBody):
    availability = get_firestore()
    if availability.client is None:
        raise HTTPException(status_code=503, detail=availability.reason or "firestore unavailable")

    db = availability.client

    try:
        from firebase_admin import firestore as admin_firestore
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"firebase-admin unavailable: {e}")

    gym_ref = db.collection("gyms").document(gym_id)
    member_ref = gym_ref.collection("members").document(body.userId)
    user_ref = db.collection("users").document(body.userId)

    transaction = db.transaction()

    @admin_firestore.transactional
    def _run(txn):
        member_snap = member_ref.get(transaction=txn)
        if member_snap.exists:
            return {"status": "already_member"}

        txn.set(member_ref, {"joinedAt": admin_firestore.SERVER_TIMESTAMP})
        txn.set(gym_ref, {"memberCount": admin_firestore.Increment(1)}, merge=True)
        txn.set(gym_ref, {"users": admin_firestore.ArrayUnion([body.userId])}, merge=True)
        txn.set(user_ref, {"gymMemberships": admin_firestore.ArrayUnion([gym_id])}, merge=True)
        return {"status": "joined"}

    result = _run(transaction)
    return {**result, "gymId": gym_id, "userId": body.userId, "timestamp": datetime.now(timezone.utc).isoformat()}

