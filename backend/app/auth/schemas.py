from pydantic import BaseModel, Field

from app.auth.constants import AUTH_TOKEN_TYPE


class UserCreate(BaseModel):
  name: str = Field(min_length=1)
  email: str = Field(min_length=3)
  password: str = Field(min_length=1)


class UserLogin(BaseModel):
  email: str = Field(min_length=3)
  password: str = Field(min_length=1)


class UserResponse(BaseModel):
  id: str
  name: str
  email: str
  created_at: str


class TokenResponse(BaseModel):
  access_token: str
  token_type: str = AUTH_TOKEN_TYPE
