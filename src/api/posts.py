from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.firestore_client import get_firestore


router = APIRouter(prefix="/api/posts", tags=["posts"])


class LikeBody(BaseModel):
    userId: str


@router.post("/{post_id}/like")
async def like_post(post_id: str, body: LikeBody):
    availability = get_firestore()
    if availability.client is None:
        raise HTTPException(status_code=503, detail=availability.reason or "firestore unavailable")

    db = availability.client

    try:
        from firebase_admin import firestore as admin_firestore
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"firebase-admin unavailable: {e}")

    post_ref = db.collection("posts").document(post_id)
    like_ref = post_ref.collection("post-likes").document(body.userId)

    transaction = db.transaction()

    @admin_firestore.transactional
    def _run(txn):
        like_snap = like_ref.get(transaction=txn)
        if like_snap.exists:
            return {"status": "already_liked"}

        txn.set(like_ref, {"createdAt": admin_firestore.SERVER_TIMESTAMP})
        txn.set(post_ref, {"likes": admin_firestore.Increment(1)}, merge=True)
        return {"status": "liked"}

    result = _run(transaction)
    return {**result, "postId": post_id, "userId": body.userId, "timestamp": datetime.now(timezone.utc).isoformat()}

