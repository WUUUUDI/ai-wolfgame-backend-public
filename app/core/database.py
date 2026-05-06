from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import datetime

from sqlalchemy import func, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# 数据库 URL（请根据实际情况修改）
DATABASE_URL = "mysql+aiomysql://root:123456@localhost:3306/ai_wolfgame?charset=utf8mb4"

# 创建异步引擎
engine = create_async_engine(DATABASE_URL, echo=True, pool_size=10, max_overflow=20)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# 基类
class Base(DeclarativeBase):
    pass

# 依赖项：获取数据库会话
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
