import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.core.database import get_conn
from app.schemas.goals import GoalCreate
from app.utils.db import execute, fetch_all
from app.utils.serialization import to_jsonable

router = APIRouter(tags=["goals"])


@router.get("/goals")
def list_goals() -> list[dict[str, Any]]:
  return fetch_all(
    """
    SELECT id, name, target_amount, achieved_amount, due_date, category, status, created_at
    FROM goals
    ORDER BY due_date ASC, created_at DESC
    """
  )


@router.post("/goals", status_code=status.HTTP_201_CREATED)
def create_goal(payload: GoalCreate) -> dict[str, Any]:
  record_id = uuid.uuid4()
  query = """
    INSERT INTO goals (id, name, target_amount, achieved_amount, due_date, category, status)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    RETURNING id, name, target_amount, achieved_amount, due_date, category, status, created_at
  """

  with get_conn() as conn:
    with conn.cursor() as cur:
      cur.execute(
        query,
        (
          record_id,
          payload.name,
          payload.target_amount,
          payload.achieved_amount,
          payload.due_date,
          payload.category,
          payload.status,
        ),
      )
      row = cur.fetchone()

  return to_jsonable(row)


@router.delete("/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(goal_id: str) -> None:
  deleted_rows = execute("DELETE FROM goals WHERE id = %s", (goal_id,))
  if deleted_rows == 0:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
