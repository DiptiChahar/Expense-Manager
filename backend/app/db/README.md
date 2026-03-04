# Database Migrations

This project uses lightweight SQL migrations (no Alembic).

## Files
- `migrations/001_init_core_tables.sql`: core schema + baseline indexes.
- `migrations/002_migrate_and_cleanup_legacy_tables.sql`: backup, migrate legacy data, then cleanup.
- `migrations/003_harden_constraints_and_indexes.sql`: idempotent hardening of constraints/indexes.
- `migrations/004_create_users_table.sql`: users table + case-insensitive email uniqueness.
- `migrations/005_add_user_id_to_tables.sql`: ownership backfill and per-user indexing.

## Running Migrations Manually (recommended for production)

```bash
cd backend
. .venv/bin/activate
python -m app.db.migrate
```

## Auto-Apply Policy
- `AUTO_APPLY_MIGRATIONS` defaults to `true` only when `ENV=development`.
- For production, set `AUTO_APPLY_MIGRATIONS=false` and run migrations manually during deployment.

## Safety Notes
- Migrations are tracked in `schema_migrations`.
- Legacy tables are backed up before migration in `002_*`.
- Hardening migration validates data before enforcing stricter constraints.
