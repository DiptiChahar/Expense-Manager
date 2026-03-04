from pydantic import BaseModel


class DashboardSummaryResponse(BaseModel):
  total_income: float
  total_expenses: float
  balance: float
  savings_rate: float


class MonthlyExpenseTrendResponse(BaseModel):
  labels: list[str]
  values: list[float]


class CategoryBreakdownItem(BaseModel):
  category: str
  total: float


class WeeklyComparisonResponse(BaseModel):
  labels: list[str]
  thisWeek: list[float]
  lastWeek: list[float]


class MonthlyComparisonResponse(BaseModel):
  labels: list[str]
  thisPeriod: list[float]
  lastPeriod: list[float]


class ExpenseBreakdownItem(BaseModel):
  category: str
  total: float
  change_percent: float
