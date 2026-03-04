from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from app.core.config import DATABASE_URL, DB_LOCK_TIMEOUT_MS, DB_STATEMENT_TIMEOUT_MS


@contextmanager
def get_conn(statement_timeout_ms: int | None = None, lock_timeout_ms: int | None = None):
  effective_statement_timeout = DB_STATEMENT_TIMEOUT_MS if statement_timeout_ms is None else statement_timeout_ms
  effective_lock_timeout = DB_LOCK_TIMEOUT_MS if lock_timeout_ms is None else lock_timeout_ms
  options = f"-c statement_timeout={effective_statement_timeout} -c lock_timeout={effective_lock_timeout}"
  conn = psycopg.connect(DATABASE_URL, row_factory=dict_row, options=options)
  try:
    yield conn
    conn.commit()
  except Exception:
    conn.rollback()
    raise
  finally:
    conn.close()


def get_db_identity() -> dict[str, str]:
  with get_conn() as conn:
    with conn.cursor() as cur:
      cur.execute("SELECT current_database() AS db, current_user AS db_user, current_schema() AS schema")
      result = cur.fetchone()
  return {
    "db": str(result["db"]),
    "db_user": str(result["db_user"]),
    "schema": str(result["schema"]),
  }


def db_ping() -> bool:
  with get_conn() as conn:
    with conn.cursor() as cur:
      cur.execute("SELECT 1 AS db_ok")
      result = cur.fetchone()
  return bool(result and result["db_ok"] == 1)
