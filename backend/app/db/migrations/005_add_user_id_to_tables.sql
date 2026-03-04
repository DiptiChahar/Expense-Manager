ALTER TABLE transactions ADD COLUMN IF NOT EXISTS user_id UUID;
ALTER TABLE budgets ADD COLUMN IF NOT EXISTS user_id UUID;
ALTER TABLE goals ADD COLUMN IF NOT EXISTS user_id UUID;
ALTER TABLE bills ADD COLUMN IF NOT EXISTS user_id UUID;

INSERT INTO users (name, email, password_hash)
SELECT 'Legacy Owner', 'legacy@spendsmart.internal', '!legacy_account_blocked!'
WHERE NOT EXISTS (
  SELECT 1 FROM users WHERE LOWER(email) = LOWER('legacy@spendsmart.internal')
);

DO $$
DECLARE
  legacy_user_id UUID;
BEGIN
  SELECT id INTO legacy_user_id
  FROM users
  WHERE LOWER(email) = LOWER('legacy@spendsmart.internal')
  LIMIT 1;

  IF legacy_user_id IS NULL THEN
    RAISE EXCEPTION 'Unable to resolve legacy owner user.';
  END IF;

  UPDATE transactions SET user_id = legacy_user_id WHERE user_id IS NULL;
  UPDATE budgets SET user_id = legacy_user_id WHERE user_id IS NULL;
  UPDATE goals SET user_id = legacy_user_id WHERE user_id IS NULL;
  UPDATE bills SET user_id = legacy_user_id WHERE user_id IS NULL;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'transactions_user_id_fkey'
      AND conrelid = 'transactions'::regclass
  ) THEN
    ALTER TABLE transactions
      ADD CONSTRAINT transactions_user_id_fkey
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'budgets_user_id_fkey'
      AND conrelid = 'budgets'::regclass
  ) THEN
    ALTER TABLE budgets
      ADD CONSTRAINT budgets_user_id_fkey
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'goals_user_id_fkey'
      AND conrelid = 'goals'::regclass
  ) THEN
    ALTER TABLE goals
      ADD CONSTRAINT goals_user_id_fkey
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'bills_user_id_fkey'
      AND conrelid = 'bills'::regclass
  ) THEN
    ALTER TABLE bills
      ADD CONSTRAINT bills_user_id_fkey
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT;
  END IF;
END $$;

ALTER TABLE transactions ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE budgets ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE goals ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE bills ALTER COLUMN user_id SET NOT NULL;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'budgets_category_month_unique'
      AND conrelid = 'budgets'::regclass
  ) THEN
    ALTER TABLE budgets DROP CONSTRAINT budgets_category_month_unique;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'budgets_user_category_month_unique'
      AND conrelid = 'budgets'::regclass
  ) THEN
    ALTER TABLE budgets
      ADD CONSTRAINT budgets_user_category_month_unique
      UNIQUE (user_id, category, month_start);
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_transactions_user_entry_date ON transactions (user_id, entry_date);
CREATE INDEX IF NOT EXISTS idx_transactions_user_type ON transactions (user_id, type);
CREATE INDEX IF NOT EXISTS idx_transactions_user_date_desc ON transactions (user_id, entry_date DESC);
-- Supports dashboard and analytics queries filtered by user and type
CREATE INDEX IF NOT EXISTS idx_transactions_user_type_date ON transactions (user_id, type, entry_date);

CREATE INDEX IF NOT EXISTS idx_budgets_user_month_start ON budgets (user_id, month_start);
CREATE INDEX IF NOT EXISTS idx_goals_user_due_date ON goals (user_id, due_date);
CREATE INDEX IF NOT EXISTS idx_bills_user_due_date ON bills (user_id, due_date);
