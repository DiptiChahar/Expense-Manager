from datetime import date, datetime, timedelta
from typing import Any

from fastapi import APIRouter

from app.utils.db import fetch_all

router = APIRouter(tags=["statistics"])


@router.get("/statistics/monthly-expense-trend")
def monthly_expense_trend() -> dict[str, list[Any]]:
  rows = fetch_all(
    """
    WITH months AS (
      SELECT generate_series(
        date_trunc('month', CURRENT_DATE) - interval '5 months',
        date_trunc('month', CURRENT_DATE),
        interval '1 month'
      )::date AS month_start
    )
    SELECT
      to_char(m.month_start, 'YYYY-MM') AS label,
      COALESCE(SUM(t.amount), 0) AS total
    FROM months m
    LEFT JOIN transactions t
      ON t.type = 'expense'
      AND date_trunc('month', t.entry_date)::date = m.month_start
    GROUP BY m.month_start
    ORDER BY m.month_start
    """
  )

  return {
    "labels": [row["label"] for row in rows],
    "values": [float(row["total"]) for row in rows],
  }


@router.get("/statistics/category-breakdown")
def category_breakdown() -> list[dict[str, Any]]:
  return fetch_all(
    """
    SELECT category, COALESCE(SUM(amount), 0) AS total
    FROM transactions
    WHERE type = 'expense'
    GROUP BY category
    ORDER BY total DESC
    LIMIT 8
    """
  )


@router.get("/statistics/weekly-comparison")
def weekly_comparison() -> dict[str, list[Any]]:
  end_date = date.today()
  start_date = end_date - timedelta(days=13)

  rows = fetch_all(
    """
    SELECT entry_date, amount
    FROM transactions
    WHERE type = 'expense'
      AND entry_date BETWEEN %s AND %s
    ORDER BY entry_date
    """,
    (start_date, end_date),
  )

  labels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

  def sunday_index(day: date) -> int:
    return (day.weekday() + 1) % 7

  start_this_week = end_date - timedelta(days=sunday_index(end_date))
  start_last_week = start_this_week - timedelta(days=7)

  this_week = [0.0] * 7
  last_week = [0.0] * 7

  for row in rows:
    entry_day = datetime.fromisoformat(row["entry_date"]).date() if isinstance(row["entry_date"], str) else row["entry_date"]
    idx = sunday_index(entry_day)
    amount = float(row["amount"])

    if start_this_week <= entry_day <= end_date:
      this_week[idx] += amount
    elif start_last_week <= entry_day < start_this_week:
      last_week[idx] += amount

  return {
    "labels": labels,
    "thisWeek": [round(val, 2) for val in this_week],
    "lastWeek": [round(val, 2) for val in last_week],
  }


@router.get("/statistics/monthly-comparison")
def monthly_comparison() -> dict[str, list[Any]]:
  rows = fetch_all(
    """
    WITH months AS (
      SELECT generate_series(1, 12) AS month_num
    ),
    this_year AS (
      SELECT EXTRACT(MONTH FROM entry_date)::int AS month_num, SUM(amount) AS total
      FROM transactions
      WHERE type = 'expense'
        AND EXTRACT(YEAR FROM entry_date) = EXTRACT(YEAR FROM CURRENT_DATE)
      GROUP BY month_num
    ),
    last_year AS (
      SELECT EXTRACT(MONTH FROM entry_date)::int AS month_num, SUM(amount) AS total
      FROM transactions
      WHERE type = 'expense'
        AND EXTRACT(YEAR FROM entry_date) = EXTRACT(YEAR FROM CURRENT_DATE) - 1
      GROUP BY month_num
    )
    SELECT
      m.month_num,
      COALESCE(ty.total, 0) AS this_total,
      COALESCE(ly.total, 0) AS last_total
    FROM months m
    LEFT JOIN this_year ty ON ty.month_num = m.month_num
    LEFT JOIN last_year ly ON ly.month_num = m.month_num
    ORDER BY m.month_num
    """
  )

  labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
  return {
    "labels": labels,
    "thisPeriod": [float(row["this_total"]) for row in rows],
    "lastPeriod": [float(row["last_total"]) for row in rows],
  }


@router.get("/expenses/breakdown")
def expenses_breakdown() -> list[dict[str, Any]]:
  return fetch_all(
    """
    WITH monthly AS (
      SELECT
        category,
        SUM(amount) FILTER (
          WHERE date_trunc('month', entry_date) = date_trunc('month', CURRENT_DATE)
        ) AS current_total,
        SUM(amount) FILTER (
          WHERE date_trunc('month', entry_date) = date_trunc('month', CURRENT_DATE - interval '1 month')
        ) AS previous_total
      FROM transactions
      WHERE type = 'expense'
      GROUP BY category
    )
    SELECT
      category,
      COALESCE(current_total, 0) AS total,
      CASE
        WHEN COALESCE(previous_total, 0) = 0 THEN 0
        ELSE ROUND(((COALESCE(current_total, 0) - previous_total) / previous_total) * 100, 2)
      END AS change_percent
    FROM monthly
    ORDER BY total DESC
    LIMIT 12
    """
  )
