import uuid
from typing import Any

import psycopg

from app.repositories.common import require_row, rows_to_jsonable


def list_bills(conn: psycopg.Connection, user_id: str) -> list[dict[str, Any]]:
  query = """
    SELECT id, vendor, amount, due_date, frequency, description, last_charge_date, status, created_at
    FROM bills
    WHERE user_id = %s
    ORDER BY due_date ASC, created_at DESC
  """
  with conn.cursor() as cur:
    cur.execute(query, (user_id,))
    return rows_to_jsonable(cur.fetchall())


def create_bill(conn: psycopg.Connection, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
  query = """
    INSERT INTO bills (id, vendor, amount, due_date, frequency, description, last_charge_date, status, user_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING id, vendor, amount, due_date, frequency, description, last_charge_date, status, created_at
  """
  with conn.cursor() as cur:
    cur.execute(
      query,
      (
        uuid.uuid4(),
        payload["vendor"],
        payload["amount"],
        payload["due_date"],
        payload["frequency"],
        payload.get("description"),
        payload.get("last_charge_date"),
        payload["status"],
        user_id,
      ),
    )
    row = cur.fetchone()

  return require_row(row, "Failed to create bill")


def delete_bill(conn: psycopg.Connection, user_id: str, bill_id: str) -> int:
  with conn.cursor() as cur:
    cur.execute("DELETE FROM bills WHERE id = %s AND user_id = %s", (bill_id, user_id))
    return cur.rowcount
