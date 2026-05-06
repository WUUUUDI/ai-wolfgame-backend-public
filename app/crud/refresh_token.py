from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.refresh_token import RefreshToken

async def create_refresh_token(db: AsyncSession, user_id: int, token_hash: str, expires_at: datetime) -> RefreshToken:
    db_token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        revoked=False
    )
    db.add(db_token)
    await db.commit()
    await db.refresh(db_token)
    return db_token

async def get_refresh_token_by_hash(db: AsyncSession, token_hash: str) -> RefreshToken | None:
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    return result.scalar_one_or_none()

async def revoke_refresh_token(db: AsyncSession, token_hash: str):
    token = await get_refresh_token_by_hash(db, token_hash)
    if token:
        token.revoked = True
        await db.commit()

async def revoke_all_user_tokens(db: AsyncSession, user_id: int):
    await db.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))
    await db.commit()