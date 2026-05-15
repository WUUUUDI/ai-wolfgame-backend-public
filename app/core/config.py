from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+aiomysql://root:123456@localhost:3306/ai_wolfgame?charset=utf8mb4"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ds_api_key: str = ""
    ds_base_url: str = "https://api.deepseek.com"

    class Config:
        env_file = ".env"

settings = Settings()