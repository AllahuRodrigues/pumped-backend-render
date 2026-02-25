from fastapi import APIRouter

from db.session import db_healthcheck


router = APIRouter(prefix="/api/db", tags=["db"])


@router.get("/health")
def health():
    ok = db_healthcheck()
    return {"status": "ok" if ok else "error", "database": "connected" if ok else "unavailable"}

