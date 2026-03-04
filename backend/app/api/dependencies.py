from collections.abc import Generator

import psycopg
from fastapi import Depends, Header, HTTPException, status
from jose.exceptions import ExpiredSignatureError, JWTError

from app.auth.auth_repository import get_user_by_id
from app.auth.constants import AUTH_TOKEN_TYPE, ERROR_INVALID_TOKEN, ERROR_TOKEN_EXPIRED, ERROR_UNAUTHORIZED
from app.auth.jwt_utils import decode_access_token
from app.core.database import get_conn


def get_db_conn() -> Generator[psycopg.Connection, None, None]:
  with get_conn() as conn:
    yield conn


def get_current_user(
  authorization: str | None = Header(default=None),
  conn: psycopg.Connection = Depends(get_db_conn),
) -> str:
  if not authorization:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail={"code": ERROR_UNAUTHORIZED, "message": "Missing authorization header"},
    )

  scheme, _, token = authorization.partition(" ")
  if scheme.lower() != AUTH_TOKEN_TYPE or not token.strip():
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail={"code": ERROR_UNAUTHORIZED, "message": "Invalid authorization header"},
    )

  try:
    payload = decode_access_token(token.strip())
  except ExpiredSignatureError as exc:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail={"code": ERROR_TOKEN_EXPIRED, "message": "Token has expired"},
    ) from exc
  except JWTError as exc:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail={"code": ERROR_INVALID_TOKEN, "message": "Invalid token"},
    ) from exc

  user_id = payload.get("sub")
  if not user_id:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail={"code": ERROR_INVALID_TOKEN, "message": "Invalid token subject"},
    )

  user = get_user_by_id(conn, str(user_id))
  if not user:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail={"code": ERROR_INVALID_TOKEN, "message": "Token subject no longer exists"},
    )

  return str(user_id)
