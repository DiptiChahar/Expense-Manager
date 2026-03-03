import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import CORS_ALLOW_ORIGINS
from app.core.database import get_db_identity
from app.routers import all_routers
from app.utils.schema_init import initialize_schema

logger = logging.getLogger(__name__)

app = FastAPI(title="SpendSmart API", version="1.0.0")

app.add_middleware(
  CORSMiddleware,
  allow_origins=CORS_ALLOW_ORIGINS,
  allow_credentials=False,
  allow_methods=["*"],
  allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
  db_identity = get_db_identity()
  initialize_schema()
  logger.info(
    "Schema initialized in database '%s' schema '%s' as user '%s'.",
    db_identity["db"],
    db_identity["schema"],
    db_identity["db_user"],
  )


for router in all_routers:
  app.include_router(router)
