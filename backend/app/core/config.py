import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"
load_dotenv(dotenv_path=ENV_FILE, override=False)

APP_NAME = "SpendSmart API"
APP_VERSION = "1.0.0"
ENV = os.getenv("ENV", "development").strip().lower()
API_V1_PREFIX = "/api/v1"

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/spendsmart")
DB_STATEMENT_TIMEOUT_MS = int(os.getenv("DB_STATEMENT_TIMEOUT_MS", "5000"))
DB_LOCK_TIMEOUT_MS = int(os.getenv("DB_LOCK_TIMEOUT_MS", "2000"))

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "").strip()
if not JWT_SECRET_KEY:
  if ENV != "development":
    raise RuntimeError("JWT_SECRET_KEY must be set when ENV is not development.")
  JWT_SECRET_KEY = "dev-jwt-secret"

JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))


def _parse_bool(value: str | None, default: bool) -> bool:
  if value is None:
    return default
  return value.strip().lower() in {"1", "true", "yes", "on"}


AUTO_APPLY_MIGRATIONS = _parse_bool(
  os.getenv("AUTO_APPLY_MIGRATIONS"),
  default=(ENV == "development"),
)

cors_origins_raw = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500")
CORS_ALLOW_ORIGINS = [origin.strip() for origin in cors_origins_raw.split(",") if origin.strip()]
