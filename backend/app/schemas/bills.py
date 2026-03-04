from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class BillCreate(BaseModel):
  vendor: str = Field(min_length=1)
  amount: float = Field(ge=0)
  due_date: date
  frequency: str = Field(min_length=1)
  description: str | None = None
  last_charge_date: date | None = None
  status: Literal["pending", "paid", "overdue"] = "pending"


class BillResponse(BaseModel):
  id: str
  vendor: str
  amount: float
  due_date: str
  frequency: str
  description: str | None = None
  last_charge_date: str | None = None
  status: Literal["pending", "paid", "overdue"]
  created_at: str
