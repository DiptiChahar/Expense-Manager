from app.core.database import get_conn
from app.models.sql_models import SCHEMA_FILE


def initialize_schema() -> None:
  schema_sql = SCHEMA_FILE.read_text(encoding="utf-8")
  with get_conn() as conn:
    with conn.cursor() as cur:
      cur.execute(schema_sql)
