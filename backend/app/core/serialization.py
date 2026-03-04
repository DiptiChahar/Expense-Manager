import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any


def to_jsonable(value: Any) -> Any:
  if isinstance(value, Decimal):
    return float(value)
  if isinstance(value, (datetime, date)):
    return value.isoformat()
  if isinstance(value, uuid.UUID):
    return str(value)
  if isinstance(value, list):
    return [to_jsonable(item) for item in value]
  if isinstance(value, dict):
    return {key: to_jsonable(val) for key, val in value.items()}
  return value
