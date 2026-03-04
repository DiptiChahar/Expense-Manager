from datetime import date

from pydantic import BaseModel, Field


class BudgetCreate(BaseModel):
  category: str = Field(min_length=1)
  monthly_limit: float = Field(ge=0)
  month_start: date
  notes: str | None = None


class BudgetResponse(BaseModel):
  id: str
  category: str
  monthly_limit: float
  month_start: str
  notes: str | None = None
  created_at: str
  spent: float | None = None
