import uvicorn
from fastapi import FastAPI
from app.api import auth

from app.core.exceptions import global_exception_handler

app = FastAPI()

app.include_router(auth.router, prefix="/api/v1")
app.add_exception_handler(Exception, global_exception_handler)

@app.get("/")
async def root():
    return {"message": "Hello "}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)