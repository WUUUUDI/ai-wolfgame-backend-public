from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.common import BizResponse
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.schemas.token import Token
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=BizResponse[UserResponse])
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    return await auth_service.register_user(db, user_data)

@router.post("/login", response_model=BizResponse[Token])
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    return await auth_service.login_user(db, login_data)

@router.post("/refresh", response_model=BizResponse[Token])
async def refresh(refresh_token: str = Body(..., embed=True), db: AsyncSession = Depends(get_db)):
    # 使用 Body 接收 JSON 格式 { "refresh_token": "..." }
    return await auth_service.refresh_access_token(db, refresh_token)

@router.post("/logout", response_model=BizResponse[dict])
async def logout(refresh_token: str = Body(..., embed=True), db: AsyncSession = Depends(get_db)):
    return await auth_service.logout_user(db, refresh_token)