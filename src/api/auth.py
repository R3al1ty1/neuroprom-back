from datetime import timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from core.db_helper import db_helper
from core.schemas.user import UserCreate, UserResponse
from auth.jwt import create_access_token, security, decode_token
import crud.user as user_crud

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: AsyncSession = Depends(db_helper.session_getter)):
    # Проверяем, существует ли пользователь с таким email
    existing_user = await user_crud.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Создаем нового пользователя
    user = await user_crud.create_user(db, user_data.email, user_data.password)
    return user

@router.post("/login")
async def login(user_data: UserCreate, db: AsyncSession = Depends(db_helper.session_getter)):
    user = await user_crud.authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Создаем токен доступа
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=timedelta(minutes=30)
    )
    return {"access_token": access_token, "token_type": "bearer"}

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(db_helper.session_getter)
) -> Optional[UserResponse]:
    token_data = decode_token(credentials.credentials)
    user = await user_crud.get_user_by_id(db, UUID(token_data["sub"]))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user