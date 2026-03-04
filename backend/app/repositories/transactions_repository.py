import uuid
from typing import Any, Literal

import psycopg

from app.core.constants.transactions import TX_STATUS_SUBMITTED, TX_TYPE_EXPENSE, TX_TYPE_INCOME
from app.repositories.common import require_row, row_to_jsonable, rows_to_jsonable

TRANSACTION_SELECT_COLUMNS = """
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
"""

TRANSACTION_INSERT_COLUMNS = """
  id,
  type,
  amount,
  category,
  merchant,
  source,
  description,
  payment_method,
  status,
  entry_date
"""


def list_transactions(
  conn: psycopg.Connection,
  user_id: str,
  tx_type: Literal[TX_TYPE_INCOME, TX_TYPE_EXPENSE] | None = None,
) -> list[dict[str, Any]]:
  query = f"SELECT {TRANSACTION_SELECT_COLUMNS} FROM transactions WHERE user_id = %s"
  params: tuple[Any, ...] = (user_id,)

  if tx_type:
    query += " AND type = %s"
    params = (user_id, tx_type)

  query += " ORDER BY entry_date DESC, created_at DESC"

  with conn.cursor() as cur:
    cur.execute(query, params)
    return rows_to_jsonable(cur.fetchall())


def create_transaction(conn: psycopg.Connection, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
  transaction_insert_columns = f"{TRANSACTION_INSERT_COLUMNS},\n  user_id"
  query = f"""
    INSERT INTO transactions ({transaction_insert_columns})
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING {TRANSACTION_SELECT_COLUMNS}
  """
  params = (
    uuid.uuid4(),
    payload["type"],
    payload["amount"],
    payload["category"],
    payload.get("merchant"),
    payload.get("source"),
    payload.get("description"),
    payload.get("payment_method"),
    payload.get("status", TX_STATUS_SUBMITTED),
    payload["entry_date"],
    user_id,
  )

  with conn.cursor() as cur:
    cur.execute(query, params)
    row = cur.fetchone()

  return require_row(row, "Failed to create transaction")


def update_transaction(
  conn: psycopg.Connection,
  user_id: str,
  transaction_id: str,
  payload: dict[str, Any],
) -> dict[str, Any] | None:
  query = f"""
    UPDATE transactions
    SET
      type = %s,
      amount = %s,
      category = %s,
      merchant = %s,
      source = %s,
      description = %s,
      payment_method = %s,
      status = %s,
      entry_date = %s
    WHERE id = %s AND user_id = %s
    RETURNING {TRANSACTION_SELECT_COLUMNS}
  """
  params = (
    payload["type"],
    payload["amount"],
    payload["category"],
    payload.get("merchant"),
    payload.get("source"),
    payload.get("description"),
    payload.get("payment_method"),
    payload.get("status", TX_STATUS_SUBMITTED),
    payload["entry_date"],
    transaction_id,
    user_id,
  )

  with conn.cursor() as cur:
    cur.execute(query, params)
    row = cur.fetchone()

  return row_to_jsonable(row)


def delete_transaction(conn: psycopg.Connection, user_id: str, transaction_id: str) -> int:
  with conn.cursor() as cur:
    cur.execute("DELETE FROM transactions WHERE id = %s AND user_id = %s", (transaction_id, user_id))
    return cur.rowcount
