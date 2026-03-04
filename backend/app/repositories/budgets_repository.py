import uuid
from typing import Any

import psycopg

from app.repositories.common import require_row, rows_to_jsonable


def list_budgets(conn: psycopg.Connection, user_id: str) -> list[dict[str, Any]]:
  query = """
    SELECT
      b.id,
      b.category,
      b.monthly_limit,
      b.month_start,
      b.notes,
      b.created_at,
      COALESCE(SUM(t.amount), 0) AS spent
    FROM budgets b
    LEFT JOIN transactions t
      ON t.type = 'expense'
      AND t.user_id = b.user_id
      AND LOWER(t.category) = LOWER(b.category)
      AND date_trunc('month', t.entry_date) = date_trunc('month', b.month_start)
    WHERE b.user_id = %s
    GROUP BY b.id, b.category, b.monthly_limit, b.month_start, b.notes, b.created_at
    ORDER BY b.created_at DESC
  """
  with conn.cursor() as cur:
    cur.execute(query, (user_id,))
    return rows_to_jsonable(cur.fetchall())


def create_budget(conn: psycopg.Connection, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
  query = """
    INSERT INTO budgets (id, category, monthly_limit, month_start, notes, user_id)
    VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING id, category, monthly_limit, month_start, notes, created_at
  """
  with conn.cursor() as cur:
    cur.execute(
      query,
      (
        uuid.uuid4(),
        payload["category"],
        payload["monthly_limit"],
        payload["month_start"],
        payload.get("notes"),
        user_id,
      ),
    )
    row = cur.fetchone()

  return require_row(row, "Failed to create budget")


def delete_budget(conn: psycopg.Connection, user_id: str, budget_id: str) -> int:
  with conn.cursor() as cur:
    cur.execute("DELETE FROM budgets WHERE id = %s AND user_id = %s", (budget_id, user_id))
    return cur.rowcount
