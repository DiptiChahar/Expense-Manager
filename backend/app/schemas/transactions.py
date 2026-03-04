from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from app.core.constants.transactions import TX_STATUS_NOT_SUBMITTED, TX_STATUS_SUBMITTED, TX_TYPE_EXPENSE, TX_TYPE_INCOME


class TransactionCreate(BaseModel):
  type: Literal[TX_TYPE_INCOME, TX_TYPE_EXPENSE]
  amount: float = Field(gt=0)
  category: str = Field(min_length=1)
  merchant: str | None = None
  source: str | None = None
  description: str | None = None
  payment_method: str | None = None
  entry_date: date
  status: Literal[TX_STATUS_SUBMITTED, TX_STATUS_NOT_SUBMITTED] = TX_STATUS_SUBMITTED


class TransactionUpdate(TransactionCreate):
  pass


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
  status: Literal[TX_STATUS_SUBMITTED, TX_STATUS_NOT_SUBMITTED] = TX_STATUS_NOT_SUBMITTED


class TransactionResponse(BaseModel):
  id: str
  type: Literal[TX_TYPE_INCOME, TX_TYPE_EXPENSE]
  amount: float
  category: str
  merchant: str | None = None
  source: str | None = None
  description: str | None = None
  payment_method: str | None = None
  status: Literal[TX_STATUS_SUBMITTED, TX_STATUS_NOT_SUBMITTED]
  entry_date: str
  created_at: str
