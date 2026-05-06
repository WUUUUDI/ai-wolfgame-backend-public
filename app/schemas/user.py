from pydantic import Field, BaseModel


class UserCreate(BaseModel):
    username: str = Field(..., min_length=5, max_length=12, description="username")
    password: str = Field(..., min_length=6, max_length=12, description="password")
    email: str = Field(..., min_length=5, max_length=50, description="email")

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool

    class Config:
        from_attributes = True

