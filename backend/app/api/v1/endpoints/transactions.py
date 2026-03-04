import logging
from typing import Literal

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_current_user, get_db_conn
from app.core.constants.messages import TRANSACTION_NOT_FOUND_CODE, TRANSACTION_NOT_FOUND_MESSAGE
from app.core.constants.transactions import TX_TYPE_EXPENSE, TX_TYPE_INCOME
from app.repositories.transactions_repository import create_transaction, delete_transaction, list_transactions, update_transaction
from app.schemas.common import OperationStatus
from app.schemas.transactions import TransactionCreate, TransactionResponse, TransactionUpdate

logger = logging.getLogger(__name__)

router = APIRouter(tags=["transactions"])


@router.get("/transactions", response_model=list[TransactionResponse])
def get_transactions(
  tx_type: Literal[TX_TYPE_INCOME, TX_TYPE_EXPENSE] | None = Query(default=None),
  user_id: str = Depends(get_current_user),
  conn: psycopg.Connection = Depends(get_db_conn),
) -> list[dict]:
  return list_transactions(conn, user_id, tx_type)


@router.post("/transactions", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def post_transaction(
  payload: TransactionCreate,
  user_id: str = Depends(get_current_user),
  conn: psycopg.Connection = Depends(get_db_conn),
) -> dict:
  row = create_transaction(conn, user_id, payload.model_dump())
  logger.info("transaction_created id=%s type=%s", row["id"], row["type"])
  return row


@router.put("/transactions/{transaction_id}", response_model=TransactionResponse)
def put_transaction(
  transaction_id: str,
  payload: TransactionUpdate,
  user_id: str = Depends(get_current_user),
  conn: psycopg.Connection = Depends(get_db_conn),
) -> dict:
  row = update_transaction(conn, user_id, transaction_id, payload.model_dump())
  if row is None:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail={"code": TRANSACTION_NOT_FOUND_CODE, "message": TRANSACTION_NOT_FOUND_MESSAGE},
    )

  logger.info("transaction_updated id=%s type=%s", row["id"], row["type"])
  return row


@router.delete("/transactions/{transaction_id}", response_model=OperationStatus)
def remove_transaction(
  transaction_id: str,
  user_id: str = Depends(get_current_user),
  conn: psycopg.Connection = Depends(get_db_conn),
) -> OperationStatus:
  deleted_rows = delete_transaction(conn, user_id, transaction_id)
  if deleted_rows == 0:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail={"code": TRANSACTION_NOT_FOUND_CODE, "message": TRANSACTION_NOT_FOUND_MESSAGE},
    )

  logger.info("transaction_deleted id=%s", transaction_id)
  return OperationStatus(status="deleted", id=transaction_id)
