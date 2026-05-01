import logging

import psycopg
from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_db_conn
from app.schemas.ai_chat import AiChatRequest, AiChatResponse
from app.services.ai_chat_service import generate_ai_chat_response

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ai-chat"])


@router.post("/ai-chat", response_model=AiChatResponse)
def post_ai_chat(
  payload: AiChatRequest,
  user_id: str = Depends(get_current_user),
  conn: psycopg.Connection = Depends(get_db_conn),
) -> AiChatResponse:
  result = generate_ai_chat_response(conn, user_id, payload.message)
  logger.info("ai_chat_response user_id=%s source=%s", user_id, result["source"])
  return AiChatResponse(**result)
