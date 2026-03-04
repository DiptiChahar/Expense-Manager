import logging
from pathlib import Path

from app.core.database import get_conn

logger = logging.getLogger(__name__)
MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def ensure_migration_table() -> None:
  query = """
    CREATE TABLE IF NOT EXISTS schema_migrations (
      id BIGSERIAL PRIMARY KEY,
      name TEXT NOT NULL UNIQUE,
      applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
  """
  with get_conn() as conn:
    with conn.cursor() as cur:
      cur.execute(query)


def list_migration_files() -> list[Path]:
  return sorted(MIGRATIONS_DIR.glob("*.sql"))


def get_applied_migrations() -> set[str]:
  with get_conn() as conn:
    with conn.cursor() as cur:
      cur.execute("SELECT name FROM schema_migrations")
      return {row["name"] for row in cur.fetchall()}


def apply_migration_file(path: Path) -> None:
  logger.info("migration_start name=%s", path.name)
  sql = path.read_text(encoding="utf-8")

  with get_conn(statement_timeout_ms=0, lock_timeout_ms=0) as conn:
    with conn.cursor() as cur:
      cur.execute(sql)
      cur.execute("INSERT INTO schema_migrations (name) VALUES (%s)", (path.name,))

  logger.info("migration_success name=%s", path.name)


def run_migrations() -> dict[str, int]:
  ensure_migration_table()
  applied = get_applied_migrations()
  migration_files = list_migration_files()

  applied_count = 0
  skipped_count = 0

  for path in migration_files:
    if path.name in applied:
      skipped_count += 1
      logger.info("migration_skip name=%s reason=already_applied", path.name)
      continue

    apply_migration_file(path)
    applied_count += 1

  logger.info("migration_summary applied=%s skipped=%s total=%s", applied_count, skipped_count, len(migration_files))
  return {"applied": applied_count, "skipped": skipped_count, "total": len(migration_files)}


if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
  run_migrations()
