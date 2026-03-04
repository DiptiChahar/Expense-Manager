import psycopg
from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_db_conn
from app.repositories.analytics_repository import (
  bucket_weekly_rows,
  get_category_breakdown,
  get_dashboard_totals,
  get_expenses_breakdown,
  get_monthly_comparison,
  get_monthly_expense_trend,
  get_weekly_expense_rows,
)
from app.schemas.analytics import (
  CategoryBreakdownItem,
  DashboardSummaryResponse,
  ExpenseBreakdownItem,
  MonthlyComparisonResponse,
  MonthlyExpenseTrendResponse,
  WeeklyComparisonResponse,
)

router = APIRouter(tags=["analytics"])


@router.get("/dashboard/summary", response_model=DashboardSummaryResponse)
def dashboard_summary(
  user_id: str = Depends(get_current_user),
  conn: psycopg.Connection = Depends(get_db_conn),
) -> DashboardSummaryResponse:
  row = get_dashboard_totals(conn, user_id)
  total_income = float(row.get("total_income", 0))
  total_expenses = float(row.get("total_expenses", 0))
  balance = total_income - total_expenses
  savings_rate = (balance / total_income * 100) if total_income > 0 else 0
  return DashboardSummaryResponse(
    total_income=round(total_income, 2),
    total_expenses=round(total_expenses, 2),
    balance=round(balance, 2),
    savings_rate=round(max(savings_rate, 0), 2),
  )


@router.get("/statistics/monthly-expense-trend", response_model=MonthlyExpenseTrendResponse)
def monthly_expense_trend(
  user_id: str = Depends(get_current_user),
  conn: psycopg.Connection = Depends(get_db_conn),
) -> MonthlyExpenseTrendResponse:
  rows = get_monthly_expense_trend(conn, user_id)
  return MonthlyExpenseTrendResponse(
    labels=[str(row["label"]) for row in rows],
    values=[float(row["total"]) for row in rows],
  )


@router.get("/statistics/category-breakdown", response_model=list[CategoryBreakdownItem])
def category_breakdown(
  user_id: str = Depends(get_current_user),
  conn: psycopg.Connection = Depends(get_db_conn),
) -> list[CategoryBreakdownItem]:
  rows = get_category_breakdown(conn, user_id)
  return [CategoryBreakdownItem(category=str(row["category"]), total=float(row["total"])) for row in rows]


@router.get("/statistics/weekly-comparison", response_model=WeeklyComparisonResponse)
def weekly_comparison(
  user_id: str = Depends(get_current_user),
  conn: psycopg.Connection = Depends(get_db_conn),
) -> WeeklyComparisonResponse:
  rows = get_weekly_expense_rows(conn, user_id)
  return WeeklyComparisonResponse(**bucket_weekly_rows(rows))


@router.get("/statistics/monthly-comparison", response_model=MonthlyComparisonResponse)
def monthly_comparison(
  user_id: str = Depends(get_current_user),
  conn: psycopg.Connection = Depends(get_db_conn),
) -> MonthlyComparisonResponse:
  rows = get_monthly_comparison(conn, user_id)
  return MonthlyComparisonResponse(
    labels=["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    thisPeriod=[float(row["this_total"]) for row in rows],
    lastPeriod=[float(row["last_total"]) for row in rows],
  )


@router.get("/expenses/breakdown", response_model=list[ExpenseBreakdownItem])
def expenses_breakdown(
  user_id: str = Depends(get_current_user),
  conn: psycopg.Connection = Depends(get_db_conn),
) -> list[ExpenseBreakdownItem]:
  rows = get_expenses_breakdown(conn, user_id)
  return [
    ExpenseBreakdownItem(
      category=str(row["category"]),
      total=float(row["total"]),
      change_percent=float(row["change_percent"]),
    )
    for row in rows
  ]
