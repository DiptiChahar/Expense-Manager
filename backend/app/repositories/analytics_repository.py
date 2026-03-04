from datetime import date, datetime, timedelta
from typing import Any

import psycopg

from app.core.constants.analytics import CATEGORY_LIMIT, EXPENSE_BREAKDOWN_LIMIT, MONTHLY_TREND_MONTHS, WEEKLY_LOOKBACK_DAYS
from app.repositories.common import row_to_jsonable, rows_to_jsonable


def get_dashboard_totals(conn: psycopg.Connection, user_id: str) -> dict[str, Any]:
  query = """
    SELECT
      COALESCE(SUM(amount) FILTER (WHERE type = 'income'), 0) AS total_income,
      COALESCE(SUM(amount) FILTER (WHERE type = 'expense'), 0) AS total_expenses
    FROM transactions
    WHERE user_id = %s
  """
  with conn.cursor() as cur:
    cur.execute(query, (user_id,))
    row = cur.fetchone() or {"total_income": 0, "total_expenses": 0}
  return row_to_jsonable(row) or {"total_income": 0, "total_expenses": 0}


def get_monthly_expense_trend(conn: psycopg.Connection, user_id: str) -> list[dict[str, Any]]:
  query = """
    WITH months AS (
      SELECT generate_series(
        date_trunc('month', CURRENT_DATE) - (%s::int - 1) * interval '1 month',
        date_trunc('month', CURRENT_DATE),
        interval '1 month'
      )::date AS month_start
    )
    SELECT
      to_char(m.month_start, 'YYYY-MM') AS label,
      COALESCE(SUM(t.amount), 0) AS total
    FROM months m
    LEFT JOIN transactions t
      ON t.user_id = %s
      AND t.type = 'expense'
      AND date_trunc('month', t.entry_date)::date = m.month_start
    GROUP BY m.month_start
    ORDER BY m.month_start
  """
  with conn.cursor() as cur:
    cur.execute(query, (MONTHLY_TREND_MONTHS, user_id))
    return rows_to_jsonable(cur.fetchall())


def get_category_breakdown(conn: psycopg.Connection, user_id: str) -> list[dict[str, Any]]:
  query = """
    SELECT category, COALESCE(SUM(amount), 0) AS total
    FROM transactions
    WHERE user_id = %s
      AND type = 'expense'
    GROUP BY category
    ORDER BY total DESC
    LIMIT %s
  """
  with conn.cursor() as cur:
    cur.execute(query, (user_id, CATEGORY_LIMIT))
    return rows_to_jsonable(cur.fetchall())


def get_weekly_expense_rows(conn: psycopg.Connection, user_id: str) -> list[dict[str, Any]]:
  end_date = date.today()
  start_date = end_date - timedelta(days=WEEKLY_LOOKBACK_DAYS - 1)

  query = """
    SELECT entry_date, amount
    FROM transactions
    WHERE user_id = %s
      AND type = 'expense'
      AND entry_date BETWEEN %s AND %s
    ORDER BY entry_date
  """
  with conn.cursor() as cur:
    cur.execute(query, (user_id, start_date, end_date))
    rows = rows_to_jsonable(cur.fetchall())
  return rows


def get_monthly_comparison(conn: psycopg.Connection, user_id: str) -> list[dict[str, Any]]:
  query = """
    WITH months AS (
      SELECT generate_series(1, 12) AS month_num
    ),
    this_year AS (
      SELECT EXTRACT(MONTH FROM entry_date)::int AS month_num, SUM(amount) AS total
      FROM transactions
      WHERE user_id = %s
        AND type = 'expense'
        AND EXTRACT(YEAR FROM entry_date) = EXTRACT(YEAR FROM CURRENT_DATE)
      GROUP BY month_num
    ),
    last_year AS (
      SELECT EXTRACT(MONTH FROM entry_date)::int AS month_num, SUM(amount) AS total
      FROM transactions
      WHERE user_id = %s
        AND type = 'expense'
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
  with conn.cursor() as cur:
    cur.execute(query, (user_id, user_id))
    return rows_to_jsonable(cur.fetchall())


def get_expenses_breakdown(conn: psycopg.Connection, user_id: str) -> list[dict[str, Any]]:
  query = """
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
      WHERE user_id = %s
        AND type = 'expense'
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
    LIMIT %s
  """
  with conn.cursor() as cur:
    cur.execute(query, (user_id, EXPENSE_BREAKDOWN_LIMIT))
    return rows_to_jsonable(cur.fetchall())


def bucket_weekly_rows(rows: list[dict[str, Any]]) -> dict[str, list[float] | list[str]]:
  labels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

  def sunday_index(day: date) -> int:
    return (day.weekday() + 1) % 7

  end_date = date.today()
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
    "thisWeek": [round(value, 2) for value in this_week],
    "lastWeek": [round(value, 2) for value in last_week],
  }
