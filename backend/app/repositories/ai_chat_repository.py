from typing import Any

import psycopg

from app.repositories.common import row_to_jsonable, rows_to_jsonable


def get_financial_rows(conn: psycopg.Connection, user_id: str, retrieval_plan: dict[str, Any]) -> dict[str, Any]:
  include_goals = bool(retrieval_plan.get("include_goals"))
  include_recent_examples = bool(retrieval_plan.get("include_recent_examples"))
  recent_limit = int(retrieval_plan.get("recent_limit", 5))
  category_limit = int(retrieval_plan.get("category_limit", 6))
  goal_limit = int(retrieval_plan.get("goal_limit", 5))

  with conn.cursor() as cur:
    cur.execute(
      """
        SELECT
          COALESCE(SUM(amount) FILTER (WHERE type = 'income'), 0) AS total_income,
          COALESCE(SUM(amount) FILTER (WHERE type = 'expense'), 0) AS total_expenses,
          COALESCE(SUM(amount) FILTER (WHERE type = 'income' AND entry_date >= CURRENT_DATE - interval '30 days'), 0) AS income_last_30_days,
          COALESCE(SUM(amount) FILTER (WHERE type = 'expense' AND entry_date >= CURRENT_DATE - interval '30 days'), 0) AS expenses_last_30_days,
          COALESCE(SUM(amount) FILTER (
            WHERE type = 'expense'
              AND entry_date >= CURRENT_DATE - interval '60 days'
              AND entry_date < CURRENT_DATE - interval '30 days'
          ), 0) AS expenses_previous_30_days
        FROM transactions
        WHERE user_id = %s
      """,
      (user_id,),
    )
    totals = row_to_jsonable(cur.fetchone()) or {}

    cur.execute(
      """
        SELECT
          category,
          COALESCE(SUM(amount), 0) AS total,
          COALESCE(SUM(amount) FILTER (WHERE entry_date >= CURRENT_DATE - interval '30 days'), 0) AS last_30_days,
          COALESCE(SUM(amount) FILTER (
            WHERE entry_date >= CURRENT_DATE - interval '60 days'
              AND entry_date < CURRENT_DATE - interval '30 days'
          ), 0) AS previous_30_days
        FROM transactions
        WHERE user_id = %s
          AND type = 'expense'
          AND entry_date >= CURRENT_DATE - interval '60 days'
        GROUP BY category
        ORDER BY last_30_days DESC, total DESC
        LIMIT %s
      """,
      (user_id, category_limit),
    )
    categories = rows_to_jsonable(cur.fetchall())

    recent_transactions = []
    if include_recent_examples:
      cur.execute(
        """
          SELECT entry_date, type, category, amount, description
          FROM transactions
          WHERE user_id = %s
            AND entry_date >= CURRENT_DATE - interval '30 days'
          ORDER BY entry_date DESC, created_at DESC
          LIMIT %s
        """,
        (user_id, recent_limit),
      )
      recent_transactions = rows_to_jsonable(cur.fetchall())

    cur.execute(
      """
        SELECT
          entry_date,
          COALESCE(SUM(amount), 0) AS total
        FROM transactions
        WHERE user_id = %s
          AND type = 'expense'
          AND entry_date >= CURRENT_DATE - interval '30 days'
        GROUP BY entry_date
        ORDER BY entry_date
      """,
      (user_id,),
    )
    daily_expenses = rows_to_jsonable(cur.fetchall())

    goals = []
    if include_goals:
      cur.execute(
        """
          SELECT name, target_amount, achieved_amount, due_date, category, status
          FROM goals
          WHERE user_id = %s
          ORDER BY due_date ASC, created_at DESC
          LIMIT %s
        """,
        (user_id, goal_limit),
      )
      goals = rows_to_jsonable(cur.fetchall())

  return {
    "totals": totals,
    "categories": categories,
    "recent_transactions": recent_transactions,
    "daily_expenses": daily_expenses,
    "goals": goals,
    "retrieval_meta": {
      "category_rows": len(categories),
      "recent_transaction_rows": len(recent_transactions),
      "daily_expense_rows": len(daily_expenses),
      "goal_rows": len(goals),
    },
  }


def find_relevant_transactions(
  conn: psycopg.Connection,
  user_id: str,
  *,
  tx_type: str | None = None,
  category: str | None = None,
  amount: float | None = None,
  entry_date: str | None = None,
  limit: int = 5,
) -> list[dict[str, Any]]:
  query = """
    SELECT
      id,
      type,
      amount,
      category,
      merchant,
      source,
      description,
      payment_method,
      status,
      entry_date,
      created_at
    FROM transactions
    WHERE user_id = %s
      AND entry_date >= CURRENT_DATE - interval '365 days'
  """
  params: list[Any] = [user_id]

  if tx_type:
    query += " AND type = %s"
    params.append(tx_type)
  if category:
    query += """
      AND (
        LOWER(category) LIKE %s
        OR LOWER(COALESCE(description, '')) LIKE %s
        OR LOWER(COALESCE(merchant, '')) LIKE %s
        OR LOWER(COALESCE(source, '')) LIKE %s
      )
    """
    like_category = f"%{category.lower()}%"
    params.extend([like_category, like_category, like_category, like_category])
  if amount is not None:
    query += " AND ABS(amount - %s) <= 0.01"
    params.append(amount)
  if entry_date:
    query += " AND entry_date = %s"
    params.append(entry_date)

  query += " ORDER BY entry_date DESC, created_at DESC LIMIT %s"
  params.append(limit)

  with conn.cursor() as cur:
    cur.execute(query, tuple(params))
    return rows_to_jsonable(cur.fetchall())
