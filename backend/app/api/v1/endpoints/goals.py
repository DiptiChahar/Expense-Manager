import logging

import psycopg
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user, get_db_conn
from app.core.constants.messages import GOAL_NOT_FOUND_MESSAGE
from app.repositories.goals_repository import create_goal, delete_goal, list_goals
from app.schemas.common import OperationStatus
from app.schemas.goals import GoalCreate, GoalResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["goals"])


@router.get("/goals", response_model=list[GoalResponse])
def get_goals(user_id: str = Depends(get_current_user), conn: psycopg.Connection = Depends(get_db_conn)) -> list[dict]:
  return list_goals(conn, user_id)


@router.post("/goals", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def post_goal(
  payload: GoalCreate,
  user_id: str = Depends(get_current_user),
  conn: psycopg.Connection = Depends(get_db_conn),
) -> dict:
  row = create_goal(conn, user_id, payload.model_dump())
  logger.info("goal_created id=%s", row["id"])
  return row


@router.delete("/goals/{goal_id}", response_model=OperationStatus)
def remove_goal(
  goal_id: str,
  user_id: str = Depends(get_current_user),
  conn: psycopg.Connection = Depends(get_db_conn),
) -> OperationStatus:
  deleted_rows = delete_goal(conn, user_id, goal_id)
  if deleted_rows == 0:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=GOAL_NOT_FOUND_MESSAGE)

  logger.info("goal_deleted id=%s", goal_id)
  return OperationStatus(status="deleted", id=goal_id)
