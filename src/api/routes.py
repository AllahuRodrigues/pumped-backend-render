from fastapi import APIRouter, Depends
from core.config import settings

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/health")
def health():
    """
    App health (no external dependencies).
    """
    return {"status": "ok", "app": settings.APP_NAME}