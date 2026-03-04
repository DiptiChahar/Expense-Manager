import logging

import psycopg
from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_user, get_db_conn
from app.core.constants.transactions import TX_TYPE_INCOME
from app.repositories.transactions_repository import list_transactions
from app.schemas.transactions import IncomeCreate, TransactionResponse
from app.services.transactions_service import create_income_transaction

logger = logging.getLogger(__name__)

router = APIRouter(tags=["income"])


@router.get("/income", response_model=list[TransactionResponse])
def get_income(user_id: str = Depends(get_current_user), conn: psycopg.Connection = Depends(get_db_conn)) -> list[dict]:
  return list_transactions(conn, user_id, TX_TYPE_INCOME)


@router.post("/income", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def post_income(
  payload: IncomeCreate,
  user_id: str = Depends(get_current_user),
  conn: psycopg.Connection = Depends(get_db_conn),
) -> dict:
  row = create_income_transaction(conn, user_id, payload)
  logger.info("income_created id=%s", row["id"])
  return row
