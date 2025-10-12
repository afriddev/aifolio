from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from app.controllers import (
    ChatRouter,
    WebSocketRouterController,
    ApiKeysRouter,
    ChatbotRouter,
)
from app import webSocket
from fastapi import WebSocket, WebSocketDisconnect
import json
from database import psqlDbClient
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(psqlDbClient.connect())
    yield
    try:
        await asyncio.wait_for(psqlDbClient.close(), timeout=3)
    except asyncio.TimeoutError:
        print("⚠️ DB close timed out")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(ChatRouter, prefix="/api/v1")
app.include_router(ApiKeysRouter, prefix="/api/v1")
app.include_router(ChatbotRouter, prefix="/api/v1")

webSocketRouter = WebSocketRouterController()


@app.websocket("/ws/{email}")
async def websocket_endpoint(websocket: WebSocket, email: str):
    await webSocket.connect(websocket, email)
    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                webSocketRouter.RouteMessage(data)
            except asyncio.TimeoutError:
                await websocket.send_text(json.dumps({"type": "ping"}))
                continue

    except WebSocketDisconnect as e:
        print(e)
        await webSocket.disconnect(email)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=False)
