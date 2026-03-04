import psycopg
from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_user, get_db_conn
from app.auth.auth_service import get_me, login_user, register_user
from app.auth.schemas import TokenResponse, UserCreate, UserLogin, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, conn: psycopg.Connection = Depends(get_db_conn)) -> TokenResponse:
  return TokenResponse(**register_user(conn, payload))


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, conn: psycopg.Connection = Depends(get_db_conn)) -> TokenResponse:
  return TokenResponse(**login_user(conn, payload))


@router.get("/me", response_model=UserResponse)
def me(user_id: str = Depends(get_current_user), conn: psycopg.Connection = Depends(get_db_conn)) -> UserResponse:
  return UserResponse(**get_me(conn, user_id))
