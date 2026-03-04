import logging

import psycopg
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user, get_db_conn
from app.core.constants.messages import BUDGET_NOT_FOUND_MESSAGE
from app.repositories.budgets_repository import create_budget, delete_budget, list_budgets
from app.schemas.budgets import BudgetCreate, BudgetResponse
from app.schemas.common import OperationStatus

logger = logging.getLogger(__name__)

router = APIRouter(tags=["budgets"])


@router.get("/budgets", response_model=list[BudgetResponse])
def get_budgets(user_id: str = Depends(get_current_user), conn: psycopg.Connection = Depends(get_db_conn)) -> list[dict]:
  return list_budgets(conn, user_id)


@router.post("/budgets", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def post_budget(
  payload: BudgetCreate,
  user_id: str = Depends(get_current_user),
  conn: psycopg.Connection = Depends(get_db_conn),
) -> dict:
  row = create_budget(conn, user_id, payload.model_dump())
  logger.info("budget_created id=%s category=%s", row["id"], row["category"])
  return row


@router.delete("/budgets/{budget_id}", response_model=OperationStatus)
def remove_budget(
  budget_id: str,
  user_id: str = Depends(get_current_user),
  conn: psycopg.Connection = Depends(get_db_conn),
) -> OperationStatus:
  deleted_rows = delete_budget(conn, user_id, budget_id)
  if deleted_rows == 0:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=BUDGET_NOT_FOUND_MESSAGE)

  logger.info("budget_deleted id=%s", budget_id)
  return OperationStatus(status="deleted", id=budget_id)
