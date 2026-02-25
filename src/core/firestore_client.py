from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class FirestoreAvailability:
    client: Optional[Any]
    reason: Optional[str] = None


def get_firestore() -> FirestoreAvailability:
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
    except Exception as e:
        return FirestoreAvailability(client=None, reason=f"firebase-admin not installed: {e}")

    if not firebase_admin._apps:
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        try:
            if creds_path:
                firebase_admin.initialize_app(credentials.Certificate(creds_path))
            else:
                firebase_admin.initialize_app()
        except Exception as e:
            return FirestoreAvailability(client=None, reason=f"firebase init failed: {e}")

    try:
        return FirestoreAvailability(client=firestore.client())
    except Exception as e:
        return FirestoreAvailability(client=None, reason=f"firestore client failed: {e}")

