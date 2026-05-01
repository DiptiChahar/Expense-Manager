import json
import logging
import re
import time
import urllib.error
import urllib.request
from collections import defaultdict, deque
from datetime import date, timedelta
from typing import Any

import psycopg

from app.core.config import (
  AI_CONTEXT_CACHE_SECONDS,
  AI_CURRENCY_SYMBOL,
  OPENAI_API_KEY,
  OPENAI_API_TIMEOUT_SECONDS,
  OPENAI_MODEL,
)
from app.core.constants.transactions import TX_STATUS_SUBMITTED, TX_TYPE_EXPENSE, TX_TYPE_INCOME
from app.repositories.ai_chat_repository import find_relevant_transactions, get_financial_rows

logger = logging.getLogger(__name__)

MAX_MEMORY_MESSAGES = 6
REQUIRED_RESPONSE_HEADINGS = ("🔍 Key Insight:", "⚠️ Problem:", "💡 Suggestions:")
_context_cache: dict[str, dict[str, Any]] = {}
_message_memory: defaultdict[str, deque[dict[str, str]]] = defaultdict(lambda: deque(maxlen=MAX_MEMORY_MESSAGES))
_action_memory: dict[str, dict[str, Any]] = {}

EXPENSE_HINTS = (
  "spent", "spend", "paid", "bought", "buy", "expense", "cost", "charged", "gave",
)
INCOME_HINTS = (
  "earned", "earn", "received", "receive", "salary", "income", "credited", "deposit", "bonus", "paid me",
)
DELETE_HINTS = ("delete", "remove", "erase", "discard")
UPDATE_HINTS = ("change", "update", "edit", "modify", "correct", "set")
KNOWN_CATEGORIES = (
  "food", "rent", "shopping", "salary", "travel", "transport", "grocery", "groceries",
  "electricity", "water", "bill", "bills", "entertainment", "medical", "health",
  "education", "fuel", "subscription", "phone", "loan", "emi", "home", "market",
)


def clear_ai_context_cache(user_id: str) -> None:
  for cache_key in list(_context_cache.keys()):
    if cache_key.startswith(f"{user_id}:"):
      _context_cache.pop(cache_key, None)


def _format_action_money(value: float | None) -> str:
  if value is None:
    return f"{AI_CURRENCY_SYMBOL} 0"
  return f"{AI_CURRENCY_SYMBOL} {float(value):,.0f}"


def _normalize_category(value: str | None) -> str | None:
  if not value:
    return None
  cleaned = re.sub(r"[^a-zA-Z0-9\s-]", "", value).strip().lower()
  cleaned = re.sub(r"\s+", " ", cleaned)
  if not cleaned:
    return None
  aliases = {
    "groceries": "grocery",
    "wages": "salary",
    "pay": "salary",
    "bills": "bill",
  }
  return aliases.get(cleaned, cleaned)


def _parse_amount(message: str) -> float | None:
  patterns = (
    r"(?:₹|rs\.?|inr|\$)\s*([0-9][0-9,]*(?:\.\d+)?)",
    r"([0-9][0-9,]*(?:\.\d+)?)\s*(?:rupees|rs|inr)",
    r"\b([0-9][0-9,]*(?:\.\d+)?)\b",
  )
  for pattern in patterns:
    match = re.search(pattern, message, flags=re.IGNORECASE)
    if not match:
      continue
    value = float(match.group(1).replace(",", ""))
    return value if value > 0 else None
  return None


def _parse_entry_date(message: str) -> str | None:
  lowered = message.lower()
  today = date.today()
  if "yesterday" in lowered:
    return (today - timedelta(days=1)).isoformat()
  if "today" in lowered:
    return today.isoformat()

  iso_match = re.search(r"\b(20\d{2}-\d{1,2}-\d{1,2})\b", message)
  if iso_match:
    try:
      return date.fromisoformat(iso_match.group(1)).isoformat()
    except ValueError:
      return None

  slash_match = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](20\d{2})\b", message)
  if slash_match:
    day, month, year = (int(slash_match.group(1)), int(slash_match.group(2)), int(slash_match.group(3)))
    try:
      return date(year, month, day).isoformat()
    except ValueError:
      return None

  return None


def _detect_intent(message: str) -> str | None:
  lowered = message.lower()
  if any(token in lowered for token in DELETE_HINTS):
    return "delete"
  if any(token in lowered for token in UPDATE_HINTS):
    return "update"
  if any(token in lowered for token in INCOME_HINTS):
    return "add_income"
  if any(token in lowered for token in EXPENSE_HINTS):
    return "add_expense"
  if _parse_amount(message) is not None:
    return "add_expense"
  return None


def _infer_type(message: str, intent: str | None, category: str | None) -> str | None:
  lowered = message.lower()
  if intent == "add_income" or any(token in lowered for token in INCOME_HINTS) or category == "salary":
    return TX_TYPE_INCOME
  if intent == "add_expense" or intent in {"update", "delete"} and any(token in lowered for token in EXPENSE_HINTS):
    return TX_TYPE_EXPENSE
  if intent in {"update", "delete"} and "income" in lowered:
    return TX_TYPE_INCOME
  if intent:
    return TX_TYPE_EXPENSE
  return None


def _parse_category(message: str) -> str | None:
  lowered = message.lower()
  for pattern in (
    r"\b(?:on|for|under|as|to)\s+([a-zA-Z][a-zA-Z\s-]{1,28})",
    r"\b(?:category)\s+([a-zA-Z][a-zA-Z\s-]{1,28})",
  ):
    match = re.search(pattern, lowered)
    if match:
      raw = re.split(r"\b(?:today|yesterday|on|for|to|from|with|at|in)\b", match.group(1))[0]
      category = _normalize_category(raw)
      if category:
        return category

  for category in KNOWN_CATEGORIES:
    if re.search(rf"\b{re.escape(category)}\b", lowered):
      return _normalize_category(category)

  return None


def _parse_description(message: str, category: str | None) -> str | None:
  cleaned = re.sub(r"(?:₹|rs\.?|inr|\$)\s*[0-9][0-9,]*(?:\.\d+)?", "", message, flags=re.IGNORECASE)
  cleaned = re.sub(r"\b[0-9][0-9,]*(?:\.\d+)?\s*(?:rupees|rs|inr)?\b", "", cleaned, flags=re.IGNORECASE)
  for token in (*EXPENSE_HINTS, *INCOME_HINTS, *DELETE_HINTS, *UPDATE_HINTS, "today", "yesterday"):
    cleaned = re.sub(rf"\b{re.escape(token)}\b", "", cleaned, flags=re.IGNORECASE)
  if category:
    cleaned = re.sub(rf"\b{re.escape(category)}\b", "", cleaned, flags=re.IGNORECASE)
  cleaned = re.sub(r"\b(?:i|my|on|for|to|from|entry|transaction|expense|income)\b", "", cleaned, flags=re.IGNORECASE)
  cleaned = re.sub(r"\s+", " ", cleaned).strip(" .,-")
  return cleaned[:80] or category


def _extract_action_entities(message: str) -> dict[str, Any]:
  intent = _detect_intent(message)
  category = _parse_category(message)
  tx_type = _infer_type(message, intent, category)
  if intent == "add_income":
    tx_type = TX_TYPE_INCOME
  if intent == "add_expense":
    tx_type = TX_TYPE_EXPENSE

  return {
    "intent": intent,
    "amount": _parse_amount(message),
    "category": category,
    "type": tx_type,
    "date": _parse_entry_date(message),
    "description": _parse_description(message, category),
  }


def _merge_action_entities(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
  merged = {**base}
  for key, value in incoming.items():
    if value is not None:
      merged[key] = value
  if merged.get("intent") == "add_income":
    merged["type"] = TX_TYPE_INCOME
  if merged.get("intent") == "add_expense":
    merged["type"] = TX_TYPE_EXPENSE
  return merged


def _missing_add_fields(action: dict[str, Any]) -> list[str]:
  missing = []
  if not action.get("amount"):
    missing.append("amount")
  if not action.get("category"):
    missing.append("category")
  if not action.get("type"):
    missing.append("type")
  return missing


def _clarification_response(user_id: str, action: dict[str, Any], missing: list[str]) -> dict[str, Any]:
  _action_memory[user_id] = action
  if "amount" in missing:
    response = "What amount should I use for this transaction?"
  elif "category" in missing:
    response = "What category should I add this under?"
  elif "type" in missing:
    response = "Should this be income or an expense?"
  else:
    response = "Can you share the missing transaction detail?"
  return {"response": response, "source": "action_clarification", "pending_action": None}


def _transaction_payload(action: dict[str, Any]) -> dict[str, Any]:
  tx_type = action.get("type") or TX_TYPE_EXPENSE
  category = _normalize_category(action.get("category")) or ("salary" if tx_type == TX_TYPE_INCOME else "other")
  description = action.get("description") or category
  return {
    "type": tx_type,
    "amount": float(action["amount"]),
    "category": category,
    "merchant": description if tx_type == TX_TYPE_EXPENSE else None,
    "source": description if tx_type == TX_TYPE_INCOME else None,
    "description": description,
    "payment_method": None,
    "entry_date": action.get("date") or date.today().isoformat(),
    "status": TX_STATUS_SUBMITTED,
  }


def _find_matching_transactions(
  conn: psycopg.Connection,
  user_id: str,
  action: dict[str, Any],
) -> list[dict[str, Any]]:
  tx_type = action.get("type")
  category = _normalize_category(action.get("category"))
  amount = action.get("amount") if action.get("intent") == "delete" else None
  entry_date = action.get("date")
  return find_relevant_transactions(
    conn,
    user_id,
    tx_type=tx_type if tx_type in {TX_TYPE_INCOME, TX_TYPE_EXPENSE} else None,
    category=category,
    amount=amount,
    entry_date=entry_date,
    limit=5,
  )


def _build_add_pending_action(action: dict[str, Any]) -> dict[str, Any]:
  payload = _transaction_payload(action)
  intent = "add_income" if payload["type"] == TX_TYPE_INCOME else "add_expense"
  label = "income" if payload["type"] == TX_TYPE_INCOME else "expense"
  confirmation = (
    f"Add {_format_action_money(payload['amount'])} {label} to {payload['category']} "
    f"for {payload['entry_date']}?"
  )
  return {
    "intent": intent,
    "amount": payload["amount"],
    "category": payload["category"],
    "type": payload["type"],
    "date": payload["entry_date"],
    "description": payload.get("description"),
    "transaction_id": None,
    "endpoint": "/transactions",
    "method": "POST",
    "payload": payload,
    "confirmation": confirmation,
  }


def _build_update_pending_action(
  conn: psycopg.Connection,
  user_id: str,
  action: dict[str, Any],
) -> dict[str, Any] | str:
  if not action.get("category"):
    return "Which transaction category should I update?"
  if not action.get("amount"):
    return "What new amount should I set for that transaction?"

  matches = _find_matching_transactions(conn, user_id, action)
  if not matches:
    return "I could not find a matching transaction. Tell me the category, amount, or date to narrow it down."
  if len(matches) > 1 and not action.get("date"):
    sample = ", ".join(
      f"{row['category']} {_format_action_money(row['amount'])} on {row['entry_date']}" for row in matches[:3]
    )
    return f"I found multiple matches: {sample}. Which date should I update?"

  target = matches[0]
  payload = {
    "type": target["type"],
    "amount": float(action["amount"]),
    "category": target["category"],
    "merchant": target.get("merchant"),
    "source": target.get("source"),
    "description": target.get("description"),
    "payment_method": target.get("payment_method"),
    "entry_date": target["entry_date"],
    "status": target.get("status", TX_STATUS_SUBMITTED),
  }
  return {
    "intent": "update",
    "amount": payload["amount"],
    "category": payload["category"],
    "type": payload["type"],
    "date": payload["entry_date"],
    "description": payload.get("description"),
    "transaction_id": target["id"],
    "endpoint": f"/transactions/{target['id']}",
    "method": "PUT",
    "payload": payload,
    "confirmation": (
      f"Change {payload['category']} {payload['type']} from "
      f"{_format_action_money(target['amount'])} to {_format_action_money(payload['amount'])}?"
    ),
  }


def _build_delete_pending_action(
  conn: psycopg.Connection,
  user_id: str,
  action: dict[str, Any],
) -> dict[str, Any] | str:
  if not action.get("category") and not action.get("amount"):
    return "Which transaction should I remove? Share the category, amount, or date."

  matches = _find_matching_transactions(conn, user_id, action)
  if not matches:
    return "I could not find a matching transaction to delete. Tell me the category, amount, or date."
  if len(matches) > 1 and not action.get("date") and not action.get("amount"):
    sample = ", ".join(
      f"{row['category']} {_format_action_money(row['amount'])} on {row['entry_date']}" for row in matches[:3]
    )
    return f"I found multiple matches: {sample}. Which one should I remove?"

  target = matches[0]
  return {
    "intent": "delete",
    "amount": float(target["amount"]),
    "category": target["category"],
    "type": target["type"],
    "date": target["entry_date"],
    "description": target.get("description"),
    "transaction_id": target["id"],
    "endpoint": f"/transactions/{target['id']}",
    "method": "DELETE",
    "payload": None,
    "confirmation": (
      f"Delete {target['category']} {target['type']} of "
      f"{_format_action_money(target['amount'])} from {target['entry_date']}?"
    ),
  }


def _action_response_from_pending(pending_action: dict[str, Any]) -> dict[str, Any]:
  return {
    "response": pending_action["confirmation"],
    "source": "action_pending_confirmation",
    "pending_action": pending_action,
  }


def _maybe_build_action_response(
  conn: psycopg.Connection,
  user_id: str,
  message: str,
) -> dict[str, Any] | None:
  lowered = message.lower().strip()
  if lowered in {"cancel", "stop", "never mind", "nevermind"} and user_id in _action_memory:
    _action_memory.pop(user_id, None)
    return {"response": "Cancelled. I did not change any transaction.", "source": "action_cancelled", "pending_action": None}

  parsed = _extract_action_entities(message)
  existing = _action_memory.get(user_id)
  if existing:
    parsed = _merge_action_entities(existing, parsed)
  elif not parsed.get("intent"):
    return None

  intent = parsed.get("intent")
  if intent in {"add_expense", "add_income"}:
    if not parsed.get("date"):
      parsed["date"] = date.today().isoformat()
    missing = _missing_add_fields(parsed)
    if missing:
      return _clarification_response(user_id, parsed, missing)
    _action_memory.pop(user_id, None)
    return _action_response_from_pending(_build_add_pending_action(parsed))

  if intent == "update":
    result = _build_update_pending_action(conn, user_id, parsed)
    if isinstance(result, str):
      _action_memory[user_id] = parsed
      return {"response": result, "source": "action_clarification", "pending_action": None}
    _action_memory.pop(user_id, None)
    return _action_response_from_pending(result)

  if intent == "delete":
    result = _build_delete_pending_action(conn, user_id, parsed)
    if isinstance(result, str):
      _action_memory[user_id] = parsed
      return {"response": result, "source": "action_clarification", "pending_action": None}
    _action_memory.pop(user_id, None)
    return _action_response_from_pending(result)

  return None


def _round_money(value: Any) -> float:
  return round(float(value or 0), 2)


def _percent(numerator: float, denominator: float) -> float:
  return round((numerator / denominator * 100), 2) if denominator > 0 else 0.0


def _category_spikes(categories: list[dict[str, Any]]) -> list[dict[str, Any]]:
  spikes = []
  for item in categories:
    current = _round_money(item.get("last_30_days"))
    previous = _round_money(item.get("previous_30_days"))
    increase = current - previous

    if current <= 0:
      continue

    if previous == 0 and current > 0:
      spikes.append({
        "category": item.get("category"),
        "current_30_days": current,
        "previous_30_days": previous,
        "increase": current,
        "change_percent": None,
      })
      continue

    change_percent = _percent(increase, previous)
    if increase > 0 and change_percent >= 20:
      spikes.append({
        "category": item.get("category"),
        "current_30_days": current,
        "previous_30_days": previous,
        "increase": round(increase, 2),
        "change_percent": change_percent,
      })

  return sorted(spikes, key=lambda row: row["increase"], reverse=True)[:5]


def _daily_spikes(daily_expenses: list[dict[str, Any]]) -> list[dict[str, Any]]:
  values = [_round_money(row.get("total")) for row in daily_expenses]
  if len(values) < 4:
    return []

  average = sum(values) / len(values)
  threshold = max(average * 1.75, average + 1)
  spikes = []
  for row in daily_expenses:
    total = _round_money(row.get("total"))
    if total >= threshold:
      spikes.append({
        "date": row.get("entry_date"),
        "total": total,
        "above_average": round(total - average, 2),
      })
  return spikes[-5:]


def _goal_progress(goals: list[dict[str, Any]]) -> list[dict[str, Any]]:
  progress = []
  for goal in goals:
    target = _round_money(goal.get("target_amount"))
    achieved = _round_money(goal.get("achieved_amount"))
    progress.append({
      "name": goal.get("name"),
      "category": goal.get("category"),
      "target_amount": target,
      "achieved_amount": achieved,
      "remaining_amount": round(max(target - achieved, 0), 2),
      "progress_percent": _percent(achieved, target),
      "due_date": goal.get("due_date"),
      "status": goal.get("status"),
    })
  return progress


def _financial_query_intent(message: str) -> str:
  lowered = message.lower()
  if any(token in lowered for token in ("goal", "target", "progress")):
    return "goals"
  if any(token in lowered for token in ("save", "saving", "savings", "reduce", "cut")):
    return "savings"
  if any(token in lowered for token in ("overspend", "spending", "expense", "category", "where am i")):
    return "spending"
  if any(token in lowered for token in ("trend", "spike", "unusual", "recent", "latest", "today", "month")):
    return "trends"
  if any(token in lowered for token in ("income", "balance", "cash")):
    return "income"
  return "general"


def _retrieval_plan_for_message(message: str) -> dict[str, Any]:
  intent = _financial_query_intent(message)
  include_goals = intent in {"goals", "savings", "general"}
  include_recent_examples = intent in {"trends", "spending"} and any(
    token in message.lower() for token in ("recent", "latest", "today", "transaction", "spike", "unusual")
  )
  return {
    "intent": intent,
    "include_goals": include_goals,
    "include_recent_examples": include_recent_examples,
    "category_limit": 6,
    "goal_limit": 5 if include_goals else 0,
    "recent_limit": 5 if include_recent_examples else 0,
  }


def _compact_goal_progress(goals: list[dict[str, Any]]) -> list[dict[str, Any]]:
  return [
    {
      "name": goal["name"],
      "remaining": goal["remaining_amount"],
      "progress_pct": goal["progress_percent"],
      "due_date": goal["due_date"],
    }
    for goal in goals[:5]
  ]


def _compact_recent_transactions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
  return [
    {
      "date": row.get("entry_date"),
      "type": row.get("type"),
      "category": row.get("category"),
      "amount": _round_money(row.get("amount")),
    }
    for row in rows[:5]
  ]


def _build_context(rows: dict[str, Any]) -> dict[str, Any]:
  totals = rows["totals"]
  total_income = _round_money(totals.get("total_income"))
  total_expenses = _round_money(totals.get("total_expenses"))
  income_last_30 = _round_money(totals.get("income_last_30_days"))
  expenses_last_30 = _round_money(totals.get("expenses_last_30_days"))
  expenses_previous_30 = _round_money(totals.get("expenses_previous_30_days"))
  balance = round(total_income - total_expenses, 2)

  category_breakdown = [
    {
      "category": row.get("category"),
      "total": _round_money(row.get("total")),
      "last_30_days": _round_money(row.get("last_30_days")),
      "previous_30_days": _round_money(row.get("previous_30_days")),
      "share_of_expenses_percent": _percent(_round_money(row.get("total")), total_expenses),
    }
    for row in rows["categories"]
  ]

  return {
    "currency_symbol": AI_CURRENCY_SYMBOL,
    "total_income": total_income,
    "total_expense": total_expenses,
    "last_30_days": {
      "income": income_last_30,
      "expense": expenses_last_30,
      "previous_expense": expenses_previous_30,
      "expense_change": round(expenses_last_30 - expenses_previous_30, 2),
    },
    "balance": balance,
    "savings_rate_percent": _percent(balance, total_income) if balance > 0 else 0.0,
    "top_categories": category_breakdown[:6],
    "recent_spikes": _category_spikes(category_breakdown),
    "daily_spikes": _daily_spikes(rows["daily_expenses"]),
    "goal_progress": _compact_goal_progress(_goal_progress(rows["goals"])),
    "recent_examples": _compact_recent_transactions(rows["recent_transactions"]),
    "retrieval_meta": rows.get("retrieval_meta", {}),
  }


def _should_refresh(message: str) -> bool:
  lowered = message.lower()
  return any(token in lowered for token in ("latest", "today", "recent", "now", "current"))


def get_financial_context(conn: psycopg.Connection, user_id: str, message: str) -> dict[str, Any]:
  now = time.time()
  retrieval_plan = _retrieval_plan_for_message(message)
  cache_key = f"{user_id}:{retrieval_plan['intent']}:{int(retrieval_plan['include_goals'])}:{int(retrieval_plan['include_recent_examples'])}"
  cached = _context_cache.get(cache_key)

  if cached and cached["expires_at"] > now and not _should_refresh(message):
    logger.info(
      "ai_rag_cache_hit user_id=%s intent=%s context_bytes=%s",
      user_id,
      retrieval_plan["intent"],
      cached["context_bytes"],
    )
    return cached["context"]

  start = time.perf_counter()
  rows = get_financial_rows(conn, user_id, retrieval_plan)
  context = _build_context(rows)
  context["query_intent"] = retrieval_plan["intent"]
  context_bytes = len(json.dumps(context, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
  elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
  _context_cache[cache_key] = {
    "expires_at": now + AI_CONTEXT_CACHE_SECONDS,
    "context": context,
    "context_bytes": context_bytes,
  }
  logger.info(
    "ai_rag_retrieval user_id=%s intent=%s include_goals=%s include_recent_examples=%s rows=%s context_bytes=%s elapsed_ms=%s",
    user_id,
    retrieval_plan["intent"],
    retrieval_plan["include_goals"],
    retrieval_plan["include_recent_examples"],
    rows.get("retrieval_meta", {}),
    context_bytes,
    elapsed_ms,
  )
  return context


def _system_instructions() -> str:
  return (
    "You are SpendSmart AI, a financial assistant inside a personal finance app. "
    "Use only the provided USER FINANCIAL CONTEXT as retrieved knowledge. "
    "Give personalized, analytical, concise advice with exact category names and amounts. "
    "Identify overspending categories, unusual patterns, income-vs-expense pressure, goal progress, "
    "and specific numeric improvements. "
    "Never invent accounts, transactions, or categories that are not present. "
    "If data is sparse, say what is missing and still give the best next step from available data. "
    "Keep the answer under 150 words, use the provided currency symbol, and avoid generic budgeting tips. "
    "Return plain text only. Do not use markdown bold, tables, numbered lists, or long paragraphs. "
    "Every answer must follow exactly this structure:\n\n"
    "🔍 Key Insight:\n"
    "One or two short conversational lines.\n\n"
    "⚠️ Problem:\n"
    "• Specific category/amount/trend bullet\n"
    "• Specific category/amount/trend bullet\n\n"
    "💡 Suggestions:\n"
    "• Exact action with exact saving amount\n"
    "• Exact action with exact saving amount"
  )


def _compact_memory(memory: list[dict[str, str]]) -> list[dict[str, str]]:
  return [
    {
      "role": item["role"],
      "content": item["content"][:220],
    }
    for item in memory[-4:]
  ]


def build_prompt(user_message: str, context: dict[str, Any], memory: list[dict[str, str]]) -> str:
  compact_context = json.dumps(context, ensure_ascii=False, separators=(",", ":"))
  compact_memory = json.dumps(_compact_memory(memory), ensure_ascii=False, separators=(",", ":"))
  return (
    f"Query: {user_message}\n"
    f"Recent chat: {compact_memory}\n"
    f"Retrieved financial context: {compact_context}\n"
    "Use the context for calculations. Do not infer beyond it. "
    "Return only the required three sections with bullets under Problem and Suggestions."
  )


def _extract_output_text(response: dict[str, Any]) -> str:
  if isinstance(response.get("output_text"), str):
    return response["output_text"].strip()

  chunks = []
  for item in response.get("output", []):
    for content in item.get("content", []):
      text = content.get("text")
      if isinstance(text, str):
        chunks.append(text)
  return "\n".join(chunks).strip()


def _call_openai(prompt: str) -> str | None:
  if not OPENAI_API_KEY:
    return None

  start = time.perf_counter()
  payload = {
    "model": OPENAI_MODEL,
    "instructions": _system_instructions(),
    "input": prompt,
  }
  request = urllib.request.Request(
    "https://api.openai.com/v1/responses",
    data=json.dumps(payload).encode("utf-8"),
    headers={
      "Authorization": f"Bearer {OPENAI_API_KEY}",
      "Content-Type": "application/json",
    },
    method="POST",
  )

  try:
    with urllib.request.urlopen(request, timeout=OPENAI_API_TIMEOUT_SECONDS) as response:
      body = json.loads(response.read().decode("utf-8"))
  except urllib.error.HTTPError as exc:
    logger.warning("openai_response_error status=%s body=%s", exc.code, exc.read().decode("utf-8")[:500])
    return None
  except Exception as exc:
    logger.warning("openai_request_failed error=%s", exc.__class__.__name__)
    return None

  logger.info(
    "ai_llm_response model=%s prompt_bytes=%s elapsed_ms=%s",
    OPENAI_MODEL,
    len(prompt.encode("utf-8")),
    round((time.perf_counter() - start) * 1000, 2),
  )
  return _extract_output_text(body) or None


def _format_money(context: dict[str, Any], value: float) -> str:
  return f"{context.get('currency_symbol', '₹')} {value:,.0f}"


def _trend_text(context: dict[str, Any], current: float, previous: float) -> str:
  if previous <= 0 and current > 0:
    return f"↑ from {_format_money(context, previous)}"
  if current > previous:
    return f"↑ {_format_money(context, current - previous)} from last period"
  if current < previous:
    return f"↓ {_format_money(context, previous - current)} from last period"
  return "no change from last period"


def _cap_for_category(value: float) -> float:
  if value <= 0:
    return 0
  return round(value * 0.5, 2)


def _format_response(insight: str, problems: list[str], suggestions: list[str]) -> str:
  problem_lines = problems[:3] or ["• Add more transactions so I can identify real spending patterns."]
  suggestion_lines = suggestions[:4] or ["• Add income, expenses, and goals to unlock personalized recommendations."]

  return (
    "🔍 Key Insight:\n"
    f"{insight}\n\n"
    "⚠️ Problem:\n"
    f"{chr(10).join(problem_lines)}\n\n"
    "💡 Suggestions:\n"
    f"{chr(10).join(suggestion_lines)}"
  )


def _normalize_model_headings(text: str) -> str:
  cleaned = text.replace("**", "").replace("__", "").replace("\r\n", "\n").strip()
  replacements = (
    (r"(?:^|\s)(?:🔍\s*)?Key Insight\s*:", "\n\n🔍 Key Insight:\n"),
    (r"(?:^|\s)(?:⚠️\s*)?Problem\s*:", "\n\n⚠️ Problem:\n"),
    (r"(?:^|\s)(?:💡\s*)?Suggestions?\s*:", "\n\n💡 Suggestions:\n"),
  )

  for pattern, replacement in replacements:
    cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

  return cleaned.strip()


def _extract_section(text: str, heading: str, next_headings: tuple[str, ...]) -> str | None:
  start = text.find(heading)
  if start == -1:
    return None

  start += len(heading)
  end = len(text)
  for next_heading in next_headings:
    next_start = text.find(next_heading, start)
    if next_start != -1:
      end = min(end, next_start)

  content = text[start:end].strip()
  return content or None


def _bulletize_section(content: str) -> list[str]:
  normalized = re.sub(r"(?<!\w)\d+[.)]\s+", "• ", content.strip())
  normalized = re.sub(r"\s*•\s*", "\n• ", normalized).strip()

  if normalized.startswith("•"):
    return [line.strip() for line in normalized.splitlines() if line.strip()]

  if not normalized:
    return []

  return [f"• {normalized}"]


def _limit_words_preserving_lines(text: str, max_words: int = 150) -> str:
  used_words = 0
  output_lines = []

  for line in text.splitlines():
    words = line.split()
    if not words:
      output_lines.append("")
      continue

    remaining = max_words - used_words
    if remaining <= 0:
      break

    if len(words) <= remaining:
      output_lines.append(line)
      used_words += len(words)
      continue

    output_lines.append(" ".join(words[:remaining]).rstrip(" ,.;") + ".")
    break

  return "\n".join(output_lines).strip()


def _clean_model_response(text: str) -> str | None:
  cleaned = _normalize_model_headings(text)
  if not all(heading in cleaned for heading in REQUIRED_RESPONSE_HEADINGS):
    return None

  insight = _extract_section(cleaned, "🔍 Key Insight:", ("⚠️ Problem:", "💡 Suggestions:"))
  problem = _extract_section(cleaned, "⚠️ Problem:", ("💡 Suggestions:",))
  suggestions = _extract_section(cleaned, "💡 Suggestions:", ())
  if not insight or not problem or not suggestions:
    return None

  formatted = _format_response(
    insight=insight,
    problems=_bulletize_section(problem),
    suggestions=_bulletize_section(suggestions),
  )
  return _limit_words_preserving_lines(formatted)


def _local_analysis(message: str, context: dict[str, Any]) -> str:
  lowered_message = message.lower()
  is_goal_query = "goal" in lowered_message or "target" in lowered_message
  top_categories = context["top_categories"]
  active_categories = [category for category in top_categories if _round_money(category.get("last_30_days")) > 0]
  categories_for_analysis = active_categories or top_categories
  top = categories_for_analysis[0] if categories_for_analysis else None
  income = context["total_income"]
  expenses = context["total_expense"]
  balance = context["balance"]
  current_30 = context["last_30_days"]["expense"]
  previous_30 = context["last_30_days"]["previous_expense"]
  spikes = context["recent_spikes"]
  goals = context["goal_progress"]

  if top:
    category_names = " and ".join(str(category["category"]) for category in categories_for_analysis[:2])
    if spikes:
      insight = f"You’re spending more on {category_names} than usual this month."
    else:
      insight = f"Your main spending pressure is {category_names}, based on your latest transactions."
  elif goals and is_goal_query:
    insight = "Your goals need attention, but I need more expense data to connect them to spending habits."
  else:
    insight = "I need more transaction data before I can spot clear overspending patterns."

  problems = []
  for category in categories_for_analysis[:2]:
    current = _round_money(category.get("last_30_days")) or _round_money(category.get("total"))
    previous = _round_money(category.get("previous_30_days"))
    problems.append(
      f"• {category['category']}: {_format_money(context, current)} ({_trend_text(context, current, previous)})"
    )

  if current_30 or previous_30:
    change = current_30 - previous_30
    problems.append(
      f"• Total last-30-day spend: {_format_money(context, current_30)} "
      f"vs {_format_money(context, previous_30)} ({'up' if change >= 0 else 'down'} {_format_money(context, abs(change))})"
    )

  if is_goal_query and goals:
    weakest = min(goals, key=lambda goal: goal["progress_pct"])
    problems.append(
      f"• {weakest['name']} goal: {weakest['progress_pct']:.0f}% complete, "
      f"with {_format_money(context, weakest['remaining'])} remaining."
    )

  suggestions = []
  projected_savings = 0.0
  for category in categories_for_analysis[:2]:
    current = _round_money(category.get("last_30_days")) or _round_money(category.get("total"))
    cap = _cap_for_category(current)
    saving = round(max(current - cap, 0), 2)
    if saving > 0:
      projected_savings += saving
      suggestions.append(
        f"• Reduce {category['category']} to {_format_money(context, cap)} next 30 days "
        f"(save {_format_money(context, saving)})."
      )

  if income > 0:
    target_savings = max(round(income * 0.2, 2), projected_savings)
    suggestions.append(f"• Keep at least {_format_money(context, target_savings)} from income for savings this month.")
  elif expenses > 0:
    suggestions.append("• Add your income record so I can calculate a reliable savings target.")

  if goals:
    weakest = min(goals, key=lambda goal: goal["progress_pct"])
    amount_to_goal = projected_savings if projected_savings > 0 else min(weakest["remaining"], max(balance * 0.1, 0))
    if amount_to_goal > 0:
      suggestions.append(f"• Move {_format_money(context, amount_to_goal)} toward {weakest['name']} after cutting spend.")

  return _format_response(insight, problems, suggestions)


def generate_ai_chat_response(conn: psycopg.Connection, user_id: str, user_message: str) -> dict[str, Any]:
  start = time.perf_counter()
  message = user_message.strip()
  action_response = _maybe_build_action_response(conn, user_id, message)
  if action_response:
    _message_memory[user_id].append({"role": "user", "content": message})
    _message_memory[user_id].append({"role": "assistant", "content": action_response["response"]})
    logger.info(
      "ai_action_completed user_id=%s source=%s has_pending_action=%s elapsed_ms=%s",
      user_id,
      action_response["source"],
      bool(action_response.get("pending_action")),
      round((time.perf_counter() - start) * 1000, 2),
    )
    return action_response

  context = get_financial_context(conn, user_id, message)
  memory = list(_message_memory[user_id])
  prompt = build_prompt(message, context, memory)
  prompt_bytes = len(prompt.encode("utf-8"))
  logger.info(
    "ai_rag_prompt user_id=%s intent=%s prompt_bytes=%s context_keys=%s",
    user_id,
    context.get("query_intent"),
    prompt_bytes,
    sorted(context.keys()),
  )

  response_text = _call_openai(prompt)
  response_text = _clean_model_response(response_text) if response_text else None
  source = "openai" if response_text else "local"
  if not response_text:
    response_text = _local_analysis(message, context)

  _message_memory[user_id].append({"role": "user", "content": message})
  _message_memory[user_id].append({"role": "assistant", "content": response_text})
  logger.info(
    "ai_chat_completed user_id=%s intent=%s source=%s elapsed_ms=%s response_chars=%s",
    user_id,
    context.get("query_intent"),
    source,
    round((time.perf_counter() - start) * 1000, 2),
    len(response_text),
  )

  return {
    "response": response_text,
    "source": source,
    "pending_action": None,
  }
