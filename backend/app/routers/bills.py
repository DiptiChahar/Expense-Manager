import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.core.database import get_conn
from app.schemas.bills import BillCreate
from app.utils.db import execute, fetch_all
from app.utils.serialization import to_jsonable

router = APIRouter(tags=["bills"])


@router.get("/bills")
def list_bills() -> list[dict[str, Any]]:
  return fetch_all(
    """
    SELECT id, vendor, amount, due_date, frequency, description, last_charge_date, status, created_at
    FROM bills
    ORDER BY due_date ASC, created_at DESC
    """
  )


@router.post("/bills", status_code=status.HTTP_201_CREATED)
def create_bill(payload: BillCreate) -> dict[str, Any]:
  record_id = uuid.uuid4()
  query = """
    INSERT INTO bills (id, vendor, amount, due_date, frequency, description, last_charge_date, status)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING id, vendor, amount, due_date, frequency, description, last_charge_date, status, created_at
  """

  with get_conn() as conn:
    with conn.cursor() as cur:
      cur.execute(
        query,
        (
          record_id,
          payload.vendor,
          payload.amount,
          payload.due_date,
          payload.frequency,
          payload.description,
          payload.last_charge_date,
          payload.status,
        ),
      )
      row = cur.fetchone()

  return to_jsonable(row)


@router.delete("/bills/{bill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bill(bill_id: str) -> None:
  deleted_rows = execute("DELETE FROM bills WHERE id = %s", (bill_id,))
  if deleted_rows == 0:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")
