import logging

import psycopg
from fastapi import HTTPException, status

from app.auth.auth_repository import create_user, get_user_auth_by_email, get_user_by_id
from app.auth.constants import (
  AUTH_TOKEN_TYPE,
  ERROR_EMAIL_EXISTS,
  ERROR_PASSWORD_TOO_SHORT,
  ERROR_UNAUTHORIZED,
  LEGACY_USER_EMAIL,
  MIN_PASSWORD_LENGTH,
)
from app.auth.jwt_utils import create_access_token
from app.auth.password_utils import hash_password, verify_password
from app.auth.schemas import UserCreate, UserLogin

logger = logging.getLogger(__name__)


def _normalize_email(email: str) -> str:
  return email.strip().lower()


def _unauthorized() -> HTTPException:
  return HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail={"code": ERROR_UNAUTHORIZED, "message": "Invalid email or password"},
  )


def register_user(conn: psycopg.Connection, payload: UserCreate) -> dict[str, str]:
  normalized_email = _normalize_email(payload.email)

  if len(payload.password) < MIN_PASSWORD_LENGTH:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail={
        "code": ERROR_PASSWORD_TOO_SHORT,
        "message": f"Password must be at least {MIN_PASSWORD_LENGTH} characters",
      },
    )

  existing_user = get_user_auth_by_email(conn, normalized_email)
  if existing_user:
    raise HTTPException(
      status_code=status.HTTP_409_CONFLICT,
      detail={"code": ERROR_EMAIL_EXISTS, "message": "Email already registered"},
    )

  try:
    user = create_user(
      conn,
      name=payload.name.strip(),
      email=normalized_email,
      password_hash=hash_password(payload.password),
    )
  except psycopg.errors.UniqueViolation as exc:
    # Race-safe duplicate handling when two requests register the same email concurrently.
    raise HTTPException(
      status_code=status.HTTP_409_CONFLICT,
      detail={"code": ERROR_EMAIL_EXISTS, "message": "Email already registered"},
    ) from exc

  logger.info("auth_register_success user_id=%s", user["id"])
  token = create_access_token(user["id"])
  return {"access_token": token, "token_type": AUTH_TOKEN_TYPE}


def login_user(conn: psycopg.Connection, payload: UserLogin) -> dict[str, str]:
  normalized_email = _normalize_email(payload.email)
  user = get_user_auth_by_email(conn, normalized_email)

  if not user:
    logger.warning("auth_login_failed reason=user_not_found")
    raise _unauthorized()

  if user["email"] == LEGACY_USER_EMAIL:
    logger.warning("auth_login_failed reason=legacy_user_blocked user_id=%s", user["id"])
    raise _unauthorized()

  if not verify_password(payload.password, user["password_hash"]):
    logger.warning("auth_login_failed reason=password_mismatch user_id=%s", user["id"])
    raise _unauthorized()

  logger.info("auth_login_success user_id=%s", user["id"])
  token = create_access_token(user["id"])
  return {"access_token": token, "token_type": AUTH_TOKEN_TYPE}


def get_me(conn: psycopg.Connection, user_id: str) -> dict:
  user = get_user_by_id(conn, user_id)
  if not user:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail={"code": ERROR_UNAUTHORIZED, "message": "Unauthorized"},
    )
  return user
