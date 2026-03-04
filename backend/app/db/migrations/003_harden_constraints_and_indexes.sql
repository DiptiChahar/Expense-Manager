DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM transactions WHERE amount < 0) THEN
    RAISE EXCEPTION 'Cannot enforce transactions amount check: negative values exist.';
  END IF;
  IF EXISTS (SELECT 1 FROM budgets WHERE monthly_limit < 0) THEN
    RAISE EXCEPTION 'Cannot enforce budgets monthly_limit check: negative values exist.';
  END IF;
  IF EXISTS (SELECT 1 FROM goals WHERE target_amount < 0 OR achieved_amount < 0) THEN
    RAISE EXCEPTION 'Cannot enforce goals amount checks: negative values exist.';
  END IF;
  IF EXISTS (SELECT 1 FROM bills WHERE amount < 0) THEN
    RAISE EXCEPTION 'Cannot enforce bills amount check: negative values exist.';
  END IF;

  IF EXISTS (SELECT 1 FROM transactions WHERE type IS NULL OR status IS NULL OR category IS NULL OR entry_date IS NULL) THEN
    RAISE EXCEPTION 'Cannot enforce transactions NOT NULL constraints: null values exist.';
  END IF;
  IF EXISTS (SELECT 1 FROM budgets WHERE category IS NULL OR month_start IS NULL OR monthly_limit IS NULL) THEN
    RAISE EXCEPTION 'Cannot enforce budgets NOT NULL constraints: null values exist.';
  END IF;
  IF EXISTS (SELECT 1 FROM goals WHERE name IS NULL OR due_date IS NULL OR target_amount IS NULL OR achieved_amount IS NULL OR status IS NULL) THEN
    RAISE EXCEPTION 'Cannot enforce goals NOT NULL constraints: null values exist.';
  END IF;
  IF EXISTS (SELECT 1 FROM bills WHERE vendor IS NULL OR due_date IS NULL OR frequency IS NULL OR amount IS NULL OR status IS NULL) THEN
    RAISE EXCEPTION 'Cannot enforce bills NOT NULL constraints: null values exist.';
  END IF;
END $$;

ALTER TABLE transactions ALTER COLUMN type SET NOT NULL;
ALTER TABLE transactions ALTER COLUMN amount SET NOT NULL;
ALTER TABLE transactions ALTER COLUMN category SET NOT NULL;
ALTER TABLE transactions ALTER COLUMN status SET NOT NULL;
ALTER TABLE transactions ALTER COLUMN entry_date SET NOT NULL;

ALTER TABLE budgets ALTER COLUMN category SET NOT NULL;
ALTER TABLE budgets ALTER COLUMN monthly_limit SET NOT NULL;
ALTER TABLE budgets ALTER COLUMN month_start SET NOT NULL;

ALTER TABLE goals ALTER COLUMN name SET NOT NULL;
ALTER TABLE goals ALTER COLUMN target_amount SET NOT NULL;
ALTER TABLE goals ALTER COLUMN achieved_amount SET NOT NULL;
ALTER TABLE goals ALTER COLUMN due_date SET NOT NULL;
ALTER TABLE goals ALTER COLUMN status SET NOT NULL;

ALTER TABLE bills ALTER COLUMN vendor SET NOT NULL;
ALTER TABLE bills ALTER COLUMN amount SET NOT NULL;
ALTER TABLE bills ALTER COLUMN due_date SET NOT NULL;
ALTER TABLE bills ALTER COLUMN frequency SET NOT NULL;
ALTER TABLE bills ALTER COLUMN status SET NOT NULL;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'transactions_amount_non_negative'
      AND conrelid = 'transactions'::regclass
  ) THEN
    ALTER TABLE transactions
      ADD CONSTRAINT transactions_amount_non_negative CHECK (amount >= 0);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'transactions_type_allowed'
      AND conrelid = 'transactions'::regclass
  ) THEN
    ALTER TABLE transactions
      ADD CONSTRAINT transactions_type_allowed CHECK (type IN ('income', 'expense'));
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'transactions_status_allowed'
      AND conrelid = 'transactions'::regclass
  ) THEN
    ALTER TABLE transactions
      ADD CONSTRAINT transactions_status_allowed CHECK (status IN ('submitted', 'not_submitted'));
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'budgets_monthly_limit_non_negative'
      AND conrelid = 'budgets'::regclass
  ) THEN
    ALTER TABLE budgets
      ADD CONSTRAINT budgets_monthly_limit_non_negative CHECK (monthly_limit >= 0);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'goals_target_amount_non_negative'
      AND conrelid = 'goals'::regclass
  ) THEN
    ALTER TABLE goals
      ADD CONSTRAINT goals_target_amount_non_negative CHECK (target_amount >= 0);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'goals_achieved_amount_non_negative'
      AND conrelid = 'goals'::regclass
  ) THEN
    ALTER TABLE goals
      ADD CONSTRAINT goals_achieved_amount_non_negative CHECK (achieved_amount >= 0);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'goals_status_allowed'
      AND conrelid = 'goals'::regclass
  ) THEN
    ALTER TABLE goals
      ADD CONSTRAINT goals_status_allowed CHECK (status IN ('active', 'completed', 'paused'));
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'bills_amount_non_negative'
      AND conrelid = 'bills'::regclass
  ) THEN
    ALTER TABLE bills
      ADD CONSTRAINT bills_amount_non_negative CHECK (amount >= 0);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'bills_status_allowed'
      AND conrelid = 'bills'::regclass
  ) THEN
    ALTER TABLE bills
      ADD CONSTRAINT bills_status_allowed CHECK (status IN ('pending', 'paid', 'overdue'));
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM (
      SELECT LOWER(category) AS category_key, month_start, COUNT(*)
      FROM budgets
      GROUP BY LOWER(category), month_start
      HAVING COUNT(*) > 1
    ) duplicates
  ) THEN
    RAISE EXCEPTION 'Cannot add budgets category+month uniqueness: duplicate rows exist.';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'budgets_category_month_unique'
      AND conrelid = 'budgets'::regclass
  ) THEN
    ALTER TABLE budgets
      ADD CONSTRAINT budgets_category_month_unique UNIQUE (category, month_start);
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_transactions_entry_date ON transactions (entry_date);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions (type);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions (status);
CREATE INDEX IF NOT EXISTS idx_transactions_type_entry_date ON transactions (type, entry_date);
CREATE INDEX IF NOT EXISTS idx_transactions_category_lower ON transactions (LOWER(category));
CREATE INDEX IF NOT EXISTS idx_bills_due_date ON bills (due_date);
CREATE INDEX IF NOT EXISTS idx_goals_due_date ON goals (due_date);
CREATE INDEX IF NOT EXISTS idx_budgets_month_start ON budgets (month_start);
