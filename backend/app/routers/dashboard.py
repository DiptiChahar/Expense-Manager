from fastapi import APIRouter

from app.utils.db import fetch_one

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/summary")
def dashboard_summary() -> dict[str, float]:
  row = fetch_one(
    """
    SELECT
      COALESCE(SUM(amount) FILTER (WHERE type = 'income'), 0) AS total_income,
      COALESCE(SUM(amount) FILTER (WHERE type = 'expense'), 0) AS total_expenses
    FROM transactions
    """
  )

  total_income = float(row["total_income"] if row else 0)
  total_expenses = float(row["total_expenses"] if row else 0)
  balance = total_income - total_expenses
  savings_rate = (balance / total_income * 100) if total_income > 0 else 0

  return {
    "total_income": round(total_income, 2),
    "total_expenses": round(total_expenses, 2),
    "balance": round(balance, 2),
    "savings_rate": round(max(savings_rate, 0), 2),
  }
