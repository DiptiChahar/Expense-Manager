from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from app.core.config import DATABASE_URL


@contextmanager
def get_conn():
  conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
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
