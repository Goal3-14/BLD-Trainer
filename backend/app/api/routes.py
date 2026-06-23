"""API routes. Health check for Phase 0; cube endpoints land in Phase 1."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
