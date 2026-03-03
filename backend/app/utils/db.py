from typing import Any

from app.core.database import get_conn
from app.utils.serialization import to_jsonable


def fetch_all(query: str, params: tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
  with get_conn() as conn:
    with conn.cursor() as cur:
      cur.execute(query, params or ())
      rows = cur.fetchall()
  return [to_jsonable(row) for row in rows]


def fetch_one(query: str, params: tuple[Any, ...] | None = None) -> dict[str, Any] | None:
  with get_conn() as conn:
    with conn.cursor() as cur:
      cur.execute(query, params or ())
      row = cur.fetchone()
  return to_jsonable(row) if row else None


def execute(query: str, params: tuple[Any, ...] | None = None) -> int:
  with get_conn() as conn:
    with conn.cursor() as cur:
      cur.execute(query, params or ())
      return cur.rowcount
