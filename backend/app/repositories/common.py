from collections.abc import Iterable
from typing import Any

from app.core.serialization import to_jsonable


def row_to_jsonable(row: Any) -> dict[str, Any] | None:
  return to_jsonable(row) if row else None


def rows_to_jsonable(rows: Iterable[Any]) -> list[dict[str, Any]]:
  return [to_jsonable(row) for row in rows]


def require_row(row: Any, error_message: str) -> dict[str, Any]:
  jsonable_row = row_to_jsonable(row)
  if not jsonable_row:
    raise RuntimeError(error_message)
  return jsonable_row
