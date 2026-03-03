from datetime import date

from pydantic import BaseModel, Field


class BudgetCreate(BaseModel):
  category: str = Field(min_length=1)
  monthly_limit: float = Field(ge=0)
  month_start: date
  notes: str | None = None
