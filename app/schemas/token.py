from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: str  # user_id
    exp: int
    jti: str  # token id

class RefreshTokenCreate(BaseModel):
    user_id: int
    token_hash: str
    expires_at: int  # timestamp