from fastapi import APIRouter

from app.utils.db import fetch_one

router = APIRouter(tags=["health"])


@router.get("/")
def root() -> dict[str, str]:
  return {"service": "SpendSmart API", "status": "ok"}


@router.get("/health")
def health() -> dict[str, str]:
  db_ok = fetch_one("SELECT 'ok' AS status")
  return {"status": "ok", "db": db_ok["status"] if db_ok else "error"}
