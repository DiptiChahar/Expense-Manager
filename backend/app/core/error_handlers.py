import logging
from typing import Any

import psycopg
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.auth.constants import ERROR_UNAUTHORIZED

logger = logging.getLogger(__name__)


def _error_payload(code: str, message: str, request: Request) -> dict[str, Any]:
  request_id = request.headers.get("x-request-id")
  return {
    "error": {
      "code": code,
      "message": message,
      "request_id": request_id,
    }
  }


def _http_code_name(status_code: int) -> str:
  mapping = {
    400: "BAD_REQUEST",
    401: ERROR_UNAUTHORIZED,
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    500: "INTERNAL_ERROR",
  }
  return mapping.get(status_code, f"HTTP_{status_code}")


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
  if isinstance(exc.detail, dict):
    code = str(exc.detail.get("code", _http_code_name(exc.status_code)))
    message = str(exc.detail.get("message", "Request failed"))
    return JSONResponse(
      status_code=exc.status_code,
      content=_error_payload(code, message, request),
    )

  detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
  return JSONResponse(
    status_code=exc.status_code,
    content=_error_payload(_http_code_name(exc.status_code), detail, request),
  )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
  logger.warning(
    "validation_error method=%s path=%s errors=%s",
    request.method,
    request.url.path,
    len(exc.errors()),
  )
  return JSONResponse(
    status_code=422,
    content=_error_payload("VALIDATION_ERROR", "Request validation failed.", request),
  )


async def psycopg_exception_handler(request: Request, exc: psycopg.Error) -> JSONResponse:
  is_timeout = isinstance(exc, (psycopg.errors.QueryCanceled, psycopg.errors.LockNotAvailable))
  if is_timeout:
    logger.warning(
      "db_timeout method=%s path=%s error=%s",
      request.method,
      request.url.path,
      exc.__class__.__name__,
    )
    return JSONResponse(
      status_code=504,
      content=_error_payload("DB_TIMEOUT", "Database request timed out.", request),
    )

  if isinstance(exc, psycopg.errors.UniqueViolation):
    logger.warning(
      "db_unique_violation method=%s path=%s",
      request.method,
      request.url.path,
    )
    return JSONResponse(
      status_code=409,
      content=_error_payload("DB_CONFLICT", "Resource conflict.", request),
    )

  logger.error(
    "db_error method=%s path=%s error=%s",
    request.method,
    request.url.path,
    exc.__class__.__name__,
    exc_info=True,
  )
  return JSONResponse(
    status_code=500,
    content=_error_payload("DB_ERROR", "Database operation failed.", request),
  )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
  logger.error(
    "unhandled_error method=%s path=%s",
    request.method,
    request.url.path,
    exc_info=True,
  )
  return JSONResponse(
    status_code=500,
    content=_error_payload("INTERNAL_ERROR", "Internal server error.", request),
  )


def register_exception_handlers(app: FastAPI) -> None:
  app.add_exception_handler(HTTPException, http_exception_handler)
  app.add_exception_handler(RequestValidationError, validation_exception_handler)
  app.add_exception_handler(psycopg.Error, psycopg_exception_handler)
  app.add_exception_handler(Exception, unhandled_exception_handler)
