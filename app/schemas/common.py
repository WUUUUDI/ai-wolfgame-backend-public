from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

from error_codes import ErrorCode

# 定义泛型变量
T = TypeVar("T")

class BizResponse(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: Optional[T] = None


    @classmethod
    def success(cls, data: T = None, message: str = "success") -> "BizResponse[T]":
        return cls(code=200, data=data, message=message)

    @classmethod
    def failure(cls, code: int, message: str = "failure") -> "BizResponse[T]":
        return cls(code=code, data=None, message=message)

    @classmethod
    def from_error_code(cls, error_code: ErrorCode) -> "BizResponse":
        """使用错误码枚举创建失败响应"""
        return cls.failure(code=error_code.code, message=error_code.message)