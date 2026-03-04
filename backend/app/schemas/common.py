from pydantic import BaseModel


class ErrorItem(BaseModel):
  code: str
  message: str
  request_id: str | None = None


class ErrorResponse(BaseModel):
  error: ErrorItem


class OperationStatus(BaseModel):
  status: str
  id: str | None = None
