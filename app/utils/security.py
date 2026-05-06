import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from werkzeug.security import generate_password_hash, check_password_hash

import jwt
from passlib.context import CryptContext

from app.core.config import settings

# 临时配置（建议后续移到 config.py）
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return generate_password_hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return check_password_hash(hashed_password, plain_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token() -> str:
    """生成随机 refresh token 字符串"""
    return secrets.token_urlsafe(64)

def hash_token(token: str) -> str:
    """对 refresh token 进行 SHA256 哈希"""
    return hashlib.sha256(token.encode()).hexdigest()

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None