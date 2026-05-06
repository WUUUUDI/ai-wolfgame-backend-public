from enum import Enum

class ErrorCode(Enum):
    # 用户注册错误（40001-40099）
    USERNAME_ALREADY_EXISTS = (40001, "Username already registered")
    EMAIL_ALREADY_EXISTS = (40002, "Email already registered")
    USER_INACTIVE = (40003, "User is inactive")

    # 认证错误（40101-40199）
    INCORRECT_USERNAME_OR_PASSWORD = (40101, "Incorrect username or password")
    INVALID_OR_EXPIRED_REFRESH_TOKEN = (40102, "Invalid or expired refresh token")
    INVALID_REFRESH_TOKEN = (40103, "Invalid refresh token")

    # 通用错误（50000-）
    INTERNAL_SERVER_ERROR = (50000, "Internal server error")

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message

    