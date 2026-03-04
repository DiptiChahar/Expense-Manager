DO $$
DECLARE
  inserted_count INTEGER := 0;
BEGIN
  IF to_regclass('public.expenses') IS NOT NULL THEN
    EXECUTE 'CREATE TABLE IF NOT EXISTS public.expenses_backup_legacy AS TABLE public.expenses WITH DATA';

    INSERT INTO transactions (
      id, type, amount, category, merchant, source, description, payment_method, status, entry_date, created_at
    )
    SELECT
      e.id,
      'expense',
      e.amount,
      e.category,
      NULL,
      NULL,
      e.description,
      NULL,
      'not_submitted',
      e.date::date,
      COALESCE(e.created_at, NOW())
    FROM expenses e
    WHERE NOT EXISTS (SELECT 1 FROM transactions t WHERE t.id = e.id);

    GET DIAGNOSTICS inserted_count = ROW_COUNT;
    RAISE NOTICE 'Migrated % row(s) from expenses to transactions.', inserted_count;
  END IF;
END $$;

DO $$
DECLARE
  inserted_count INTEGER := 0;
BEGIN
  IF to_regclass('public.subscriptions') IS NOT NULL THEN
    EXECUTE 'CREATE TABLE IF NOT EXISTS public.subscriptions_backup_legacy AS TABLE public.subscriptions WITH DATA';

    INSERT INTO bills (
      id,
      vendor,
      amount,
      due_date,
      frequency,
      description,
      last_charge_date,
      status,
      created_at
    )
    SELECT
      s.id,
      s.name,
      s.amount,
      s.next_payment_date::date,
      s.frequency,
      COALESCE(NULLIF(TRIM(s.notes), ''), s.name),
      s.start_date::date,
      'pending',
      COALESCE(s.created_at, NOW())
    FROM subscriptions s
    WHERE NOT EXISTS (SELECT 1 FROM bills b WHERE b.id = s.id);

    GET DIAGNOSTICS inserted_count = ROW_COUNT;
    RAISE NOTICE 'Migrated % row(s) from subscriptions to bills.', inserted_count;
  END IF;
END $$;

DO $$
DECLARE
  inserted_count INTEGER := 0;
BEGIN
  IF to_regclass('public.savings_goals') IS NOT NULL THEN
    EXECUTE 'CREATE TABLE IF NOT EXISTS public.savings_goals_backup_legacy AS TABLE public.savings_goals WITH DATA';

    INSERT INTO goals (
      id,
      name,
      target_amount,
      achieved_amount,
      due_date,
      category,
      status,
      created_at
    )
    SELECT
      sg.id,
      sg.title,
      sg.target_amount,
      sg.current_amount,
      sg.deadline::date,
      'Savings',
      CASE
        WHEN sg.current_amount >= sg.target_amount THEN 'completed'
        ELSE 'active'
      END,
      COALESCE(sg.created_at, NOW())
    FROM savings_goals sg
    WHERE NOT EXISTS (SELECT 1 FROM goals g WHERE g.id = sg.id);

    GET DIAGNOSTICS inserted_count = ROW_COUNT;
    RAISE NOTICE 'Migrated % row(s) from savings_goals to goals.', inserted_count;
  END IF;
END $$;

DROP TABLE IF EXISTS expenses;
DROP TABLE IF EXISTS subscriptions;
DROP TABLE IF EXISTS savings_goals;
