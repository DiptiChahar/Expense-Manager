from app.routers import bills, budgets, dashboard, expenses, goals, health, income, notifications, statistics, transactions

all_routers = [
  health.router,
  transactions.router,
  income.router,
  expenses.router,
  budgets.router,
  goals.router,
  bills.router,
  dashboard.router,
  statistics.router,
  notifications.router,
]
