import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"
load_dotenv(dotenv_path=ENV_FILE, override=False)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/spendsmart")

cors_origins_raw = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:5500")
CORS_ALLOW_ORIGINS = [origin.strip() for origin in cors_origins_raw.split(",") if origin.strip()]
