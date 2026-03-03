import uuid
from typing import Any

from app.core.database import get_conn
from app.utils.serialization import to_jsonable


def create_transaction_record(payload: dict[str, Any]) -> dict[str, Any]:
  record_id = uuid.uuid4()
  query = """
    INSERT INTO transactions (
      id, type, amount, category, merchant, source, description, payment_method, status, entry_date
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING id, type, amount, category, merchant, source, description, payment_method, status, entry_date, created_at
  """
  params = (
    record_id,
    payload["type"],
    payload["amount"],
    payload["category"],
    payload.get("merchant"),
    payload.get("source"),
    payload.get("description"),
    payload.get("payment_method"),
    payload.get("status", "submitted"),
    payload["entry_date"],
  )

  with get_conn() as conn:
    with conn.cursor() as cur:
      cur.execute(query, params)
      row = cur.fetchone()

  if not row:
    raise RuntimeError("Unable to create transaction")

  return to_jsonable(row)
