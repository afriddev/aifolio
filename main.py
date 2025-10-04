# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # asyncio.create_task(psqlDbClient.connect())
#     yield
#     try:
#         print("")
#         # await asyncio.wait_for(psqlDbClient.close(), timeout=3)
#     except asyncio.TimeoutError:
#         print("⚠️ DB close timed out")

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from app.controllers import ChatRouter
from app import webSocket

app = FastAPI()

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
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
            except asyncio.TimeoutError:
                continue

    except WebSocketDisconnect:
        webSocket.disconnect(email)

    except asyncio.CancelledError:
        try:
            await websocket.close()
        except Exception:
            pass
        webSocket.disconnect(email)
        raise

    except Exception:
        webSocket.disconnect(email)
        raise


if __name__ == "__main__":
    import uvicorn

    config = uvicorn.Config(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        reload_dirs=["app"],
        reload_excludes=["node_modules", ".venv", "__pycache__"],
        reload_includes=["*.py"],
        timeout_graceful_shutdown=5,  # seconds to wait for graceful shutdown (dev-only)
    )
    server = uvicorn.Server(config)
    server.force_exit = True
    server.run()
