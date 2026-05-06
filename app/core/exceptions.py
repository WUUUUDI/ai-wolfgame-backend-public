from fastapi import Request
from fastapi.responses import JSONResponse
from app.schemas.common import BizResponse

async def global_exception_handler(request: Request, exc: Exception):

    # logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=200,
        content=BizResponse.failure(500, "Internal server error").dict()
    )