from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
  type: Literal["income", "expense"]
  amount: float = Field(gt=0)
  category: str = Field(min_length=1)
  merchant: str | None = None
  source: str | None = None
  description: str | None = None
  payment_method: str | None = None
  entry_date: date
  status: Literal["submitted", "not_submitted"] = "submitted"


class IncomeCreate(BaseModel):
  amount: float = Field(gt=0)
  source: str = Field(min_length=1)
  description: str | None = None
  entry_date: date


class ExpenseCreate(BaseModel):
  amount: float = Field(gt=0)
  category: str = Field(min_length=1)
  merchant: str | None = None
  description: str | None = None
  payment_method: str | None = None
  entry_date: date
  status: Literal["submitted", "not_submitted"] = "not_submitted"
