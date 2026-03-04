from datetime import UTC, datetime, timedelta

from jose import jwt

from app.core.config import JWT_ALGORITHM, JWT_EXPIRE_HOURS, JWT_SECRET_KEY


def create_access_token(user_id: str) -> str:
  expires_at = datetime.now(UTC) + timedelta(hours=JWT_EXPIRE_HOURS)
  payload = {
    "sub": user_id,
    "exp": expires_at,
  }
  return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
  return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
