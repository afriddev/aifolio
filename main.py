from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from database import psqlDbClient


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



if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=False)