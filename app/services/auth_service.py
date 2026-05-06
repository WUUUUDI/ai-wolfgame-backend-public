import uuid
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import user as user_crud, refresh_token as rt_crud
from app.models.user import User
from app.schemas.common import BizResponse
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.schemas.token import Token
from app.utils.security import (
    verify_password, create_access_token, create_refresh_token, hash_token, decode_token
)
from app.core.config import settings
from error_codes import ErrorCode


def _to_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        is_active=user.is_active
    )


async def register_user(db: AsyncSession, user_data: UserCreate) -> BizResponse[UserResponse]:
    existing_user = await user_crud.get_user_by_username(db, user_data.username)
    if existing_user:
        return BizResponse.from_error_code(ErrorCode.USERNAME_ALREADY_EXISTS)
    existing_email = await user_crud.get_user_by_email(db, user_data.email)
    if existing_email:
        return BizResponse.from_error_code(ErrorCode.EMAIL_ALREADY_EXISTS)

    user = await user_crud.create_user(db, user_data)
    return BizResponse.success(data=_to_user_response(user), message="User registered successfully")

async def login_user(db: AsyncSession, login_data: UserLogin) -> BizResponse[Token]:
    user = await user_crud.get_user_by_username(db, login_data.username)
    if not user or not verify_password(login_data.password, user.hashed_password):
        return BizResponse.from_error_code(ErrorCode.INCORRECT_USERNAME_OR_PASSWORD)
    if not user.is_active:
        return BizResponse.from_error_code(ErrorCode.USER_INACTIVE)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "jti": str(uuid.uuid4())},
        expires_delta=access_token_expires
    )
    raw_refresh = create_refresh_token()
    refresh_hash = hash_token(raw_refresh)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    await rt_crud.create_refresh_token(db, user.id, refresh_hash, expires_at)

    token_data = Token(access_token=access_token, refresh_token=raw_refresh)
    return BizResponse.success(data=token_data, message="Login success")

async def refresh_access_token(db: AsyncSession, refresh_token: str) -> BizResponse[Token]:
    token_hash = hash_token(refresh_token)
    stored_token = await rt_crud.get_refresh_token_by_hash(db, token_hash)
    if not stored_token or stored_token.revoked or stored_token.expires_at < datetime.now(timezone.utc):
        return BizResponse.from_error_code(ErrorCode.INVALID_OR_EXPIRED_REFRESH_TOKEN)

    new_access_token = create_access_token(
        data={"sub": str(stored_token.user_id), "jti": str(uuid.uuid4())},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    token_data = Token(access_token=new_access_token, refresh_token=refresh_token)
    return BizResponse.success(data=token_data, message="Token refreshed")

async def logout_user(db: AsyncSession, refresh_token: str) -> BizResponse[dict]:
    token_hash = hash_token(refresh_token)
    revoked_count = await rt_crud.revoke_refresh_token(db, token_hash)
    if revoked_count == 0:
        return BizResponse.from_error_code(ErrorCode.INVALID_REFRESH_TOKEN)
    return BizResponse.success(data={"msg": "Successfully logged out"}, message="Logout success")