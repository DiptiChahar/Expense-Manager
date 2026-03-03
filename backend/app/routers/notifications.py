from fastapi import APIRouter

from app.schemas.notifications import RiskNotification
from app.utils.db import fetch_all

router = APIRouter(tags=["notifications"])


@router.get("/notifications/risks", response_model=list[RiskNotification])
def risk_notifications() -> list[RiskNotification]:
  risks: list[RiskNotification] = []

  overdue_bills = fetch_all(
    """
    SELECT vendor, amount, due_date
    FROM bills
    WHERE due_date < CURRENT_DATE
      AND status <> 'paid'
    ORDER BY due_date ASC
    """
  )

  for bill in overdue_bills:
    risks.append(
      RiskNotification(
        level="high",
        message=f"Overdue bill: {bill['vendor']} (${float(bill['amount']):.2f}) due on {bill['due_date']}",
      )
    )

  over_budget_rows = fetch_all(
    """
    WITH budget_usage AS (
      SELECT
        b.category,
        b.monthly_limit,
        COALESCE(SUM(t.amount), 0) AS spent
      FROM budgets b
      LEFT JOIN transactions t
        ON t.type = 'expense'
        AND LOWER(t.category) = LOWER(b.category)
        AND date_trunc('month', t.entry_date) = date_trunc('month', CURRENT_DATE)
      GROUP BY b.category, b.monthly_limit
    )
    SELECT category, monthly_limit, spent
    FROM budget_usage
    WHERE spent > monthly_limit
    ORDER BY spent - monthly_limit DESC
    """
  )

  for row in over_budget_rows:
    risks.append(
      RiskNotification(
        level="medium",
        message=(
          f"Budget exceeded in {row['category']}: "
          f"spent ${float(row['spent']):.2f} vs limit ${float(row['monthly_limit']):.2f}"
        ),
      )
    )

  if not risks:
    risks.append(RiskNotification(level="low", message="No risk alerts right now."))

  return risks
