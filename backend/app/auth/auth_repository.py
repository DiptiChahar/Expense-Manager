import psycopg

from app.core.serialization import to_jsonable


def get_user_auth_by_email(conn: psycopg.Connection, email: str) -> dict | None:
  query = """
    SELECT id, name, email, password_hash, created_at
    FROM users
    WHERE LOWER(email) = LOWER(%s)
    LIMIT 1
  """
  with conn.cursor() as cur:
    cur.execute(query, (email,))
    row = cur.fetchone()
  return to_jsonable(row) if row else None


def get_user_by_id(conn: psycopg.Connection, user_id: str) -> dict | None:
  query = """
    SELECT id, name, email, created_at
    FROM users
    WHERE id = %s
    LIMIT 1
  """
  with conn.cursor() as cur:
    cur.execute(query, (user_id,))
    row = cur.fetchone()
  return to_jsonable(row) if row else None


def create_user(conn: psycopg.Connection, name: str, email: str, password_hash: str) -> dict:
  query = """
    INSERT INTO users (name, email, password_hash)
    VALUES (%s, %s, %s)
    RETURNING id, name, email, created_at
  """
  with conn.cursor() as cur:
    cur.execute(query, (name, email, password_hash))
    row = cur.fetchone()

  if not row:
    raise RuntimeError("Failed to create user")

  return to_jsonable(row)
