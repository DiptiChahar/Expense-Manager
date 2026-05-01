from typing import Any, Literal

from pydantic import BaseModel, Field


AiChatIntent = Literal["add_expense", "add_income", "update", "delete"]
AiChatActionMethod = Literal["POST", "PUT", "DELETE"]


class AiChatPendingAction(BaseModel):
  intent: AiChatIntent
  amount: float | None = None
  category: str | None = None
  type: Literal["income", "expense"] | None = None
  date: str | None = None
  description: str | None = None
  transaction_id: str | None = None
  endpoint: str
  method: AiChatActionMethod
  payload: dict[str, Any] | None = None
  confirmation: str


class AiChatRequest(BaseModel):
  message: str = Field(min_length=1, max_length=1000)


class AiChatResponse(BaseModel):
  response: str
  source: str
  pending_action: AiChatPendingAction | None = None
