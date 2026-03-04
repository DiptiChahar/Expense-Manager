import uuid
from typing import Any

import psycopg

from app.repositories.common import require_row, rows_to_jsonable


def list_goals(conn: psycopg.Connection, user_id: str) -> list[dict[str, Any]]:
  query = """
    SELECT id, name, target_amount, achieved_amount, due_date, category, status, created_at
    FROM goals
    WHERE user_id = %s
    ORDER BY due_date ASC, created_at DESC
  """
  with conn.cursor() as cur:
    cur.execute(query, (user_id,))
    return rows_to_jsonable(cur.fetchall())


def create_goal(conn: psycopg.Connection, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
  query = """
    INSERT INTO goals (id, name, target_amount, achieved_amount, due_date, category, status, user_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING id, name, target_amount, achieved_amount, due_date, category, status, created_at
  """
  with conn.cursor() as cur:
    cur.execute(
      query,
      (
        uuid.uuid4(),
        payload["name"],
        payload["target_amount"],
        payload["achieved_amount"],
        payload["due_date"],
        payload.get("category"),
        payload["status"],
        user_id,
      ),
    )
    row = cur.fetchone()

  return require_row(row, "Failed to create goal")


def delete_goal(conn: psycopg.Connection, user_id: str, goal_id: str) -> int:
  with conn.cursor() as cur:
    cur.execute("DELETE FROM goals WHERE id = %s AND user_id = %s", (goal_id, user_id))
    return cur.rowcount
