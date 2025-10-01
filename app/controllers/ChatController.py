from fastapi import APIRouter


ChatRouter = APIRouter()


@ChatRouter.get("/chat")
async def Chat():
    return {"message": "Chat endpoint"}
    