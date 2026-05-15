import uvicorn
from fastapi import FastAPI
from app.api import auth
from app.api.game_router import router as game_router
from app.api.game_websocket import game_websocket

from app.core.exceptions import global_exception_handler

app = FastAPI()

app.include_router(auth.router, prefix="/api/v1")
app.include_router(game_router, prefix="/api/v1")
app.add_api_websocket_route("/ws/wolf_game/{room_id}", game_websocket)
app.add_exception_handler(Exception, global_exception_handler)

@app.get("/")
async def root():
    return {"message": "Hello "}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)