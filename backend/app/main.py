import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import API_V1_PREFIX, APP_NAME, APP_VERSION, AUTO_APPLY_MIGRATIONS, CORS_ALLOW_ORIGINS, ENV
from app.core.error_handlers import register_exception_handlers
from app.core.database import get_db_identity
from app.db.migrate import run_migrations

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(title=APP_NAME, version=APP_VERSION)

app.add_middleware(
  CORSMiddleware,
  allow_origins=CORS_ALLOW_ORIGINS,
  allow_credentials=False,
  allow_methods=["*"],
  allow_headers=["*"],
)
register_exception_handlers(app)


@app.on_event("startup")
def startup() -> None:
  logger.info("app_startup env=%s auto_apply_migrations=%s", ENV, AUTO_APPLY_MIGRATIONS)
  if AUTO_APPLY_MIGRATIONS:
    run_migrations()
  else:
    logger.info("auto migrations disabled; run `python -m app.db.migrate` manually.")

  db_identity = get_db_identity()
  logger.info(
    "database_connected db=%s schema=%s user=%s",
    db_identity["db"],
    db_identity["schema"],
    db_identity["db_user"],
  )

app.include_router(api_router, prefix=API_V1_PREFIX)
