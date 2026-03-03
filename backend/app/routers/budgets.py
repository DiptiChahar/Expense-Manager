import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.core.database import get_conn
from app.schemas.budgets import BudgetCreate
from app.utils.db import execute, fetch_all
from app.utils.serialization import to_jsonable

router = APIRouter(tags=["budgets"])


@router.get("/budgets")
def list_budgets() -> list[dict[str, Any]]:
  return fetch_all(
    """
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
      AND LOWER(t.category) = LOWER(b.category)
      AND date_trunc('month', t.entry_date) = date_trunc('month', b.month_start)
    GROUP BY b.id, b.category, b.monthly_limit, b.month_start, b.notes, b.created_at
    ORDER BY b.created_at DESC
    """
  )


@router.post("/budgets", status_code=status.HTTP_201_CREATED)
def create_budget(payload: BudgetCreate) -> dict[str, Any]:
  record_id = uuid.uuid4()
  query = """
    INSERT INTO budgets (id, category, monthly_limit, month_start, notes)
    VALUES (%s, %s, %s, %s, %s)
    RETURNING id, category, monthly_limit, month_start, notes, created_at
  """

  with get_conn() as conn:
    with conn.cursor() as cur:
      cur.execute(query, (record_id, payload.category, payload.monthly_limit, payload.month_start, payload.notes))
      row = cur.fetchone()

  return to_jsonable(row)


@router.delete("/budgets/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(budget_id: str) -> None:
  deleted_rows = execute("DELETE FROM budgets WHERE id = %s", (budget_id,))
  if deleted_rows == 0:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
