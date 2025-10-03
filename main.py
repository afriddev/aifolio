from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from app.controllers import ChatRouter
from app import webSocket
from fastapi import WebSocket,WebSocketDisconnect


@asynccontextmanager
async def lifespan(app: FastAPI):
    # asyncio.create_task(psqlDbClient.connect())
    yield
    try:
        print("")
        # await asyncio.wait_for(psqlDbClient.close(), timeout=3)
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


@app.websocket("/ws/{email}")
async def websocket_endpoint(websocket: WebSocket, email: str):
    await webSocket.connect(websocket, email)
    try:
        while True:
            await asyncio.sleep(10) 
    except WebSocketDisconnect:
        webSocket.disconnect(email)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=False)
