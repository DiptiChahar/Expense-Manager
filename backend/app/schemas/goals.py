from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class GoalCreate(BaseModel):
  name: str = Field(min_length=1)
  target_amount: float = Field(ge=0)
  achieved_amount: float = Field(ge=0)
  due_date: date
  category: str | None = None
  status: Literal["active", "completed", "paused"] = "active"
