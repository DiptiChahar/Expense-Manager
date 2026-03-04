from fastapi import APIRouter

from app.core.config import APP_NAME
from app.core.database import db_ping
from app.schemas.health import HealthResponse, RootResponse

router = APIRouter(tags=["health"])


@router.get("/", response_model=RootResponse)
def root() -> RootResponse:
  return RootResponse(service=APP_NAME, status="ok")


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
  healthy = db_ping()
  return HealthResponse(status="ok" if healthy else "degraded", db="ok" if healthy else "error")
