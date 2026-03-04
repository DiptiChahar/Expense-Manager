import logging

import psycopg
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user, get_db_conn
from app.core.constants.messages import BILL_NOT_FOUND_MESSAGE
from app.repositories.bills_repository import create_bill, delete_bill, list_bills
from app.schemas.bills import BillCreate, BillResponse
from app.schemas.common import OperationStatus

logger = logging.getLogger(__name__)

router = APIRouter(tags=["bills"])


@router.get("/bills", response_model=list[BillResponse])
def get_bills(user_id: str = Depends(get_current_user), conn: psycopg.Connection = Depends(get_db_conn)) -> list[dict]:
  return list_bills(conn, user_id)


@router.post("/bills", response_model=BillResponse, status_code=status.HTTP_201_CREATED)
def post_bill(
  payload: BillCreate,
  user_id: str = Depends(get_current_user),
  conn: psycopg.Connection = Depends(get_db_conn),
) -> dict:
  row = create_bill(conn, user_id, payload.model_dump())
  logger.info("bill_created id=%s vendor=%s", row["id"], row["vendor"])
  return row


@router.delete("/bills/{bill_id}", response_model=OperationStatus)
def remove_bill(
  bill_id: str,
  user_id: str = Depends(get_current_user),
  conn: psycopg.Connection = Depends(get_db_conn),
) -> OperationStatus:
  deleted_rows = delete_bill(conn, user_id, bill_id)
  if deleted_rows == 0:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=BILL_NOT_FOUND_MESSAGE)

  logger.info("bill_deleted id=%s", bill_id)
  return OperationStatus(status="deleted", id=bill_id)
