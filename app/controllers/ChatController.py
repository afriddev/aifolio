from fastapi import APIRouter
from app.models import ChatRequestModel
from fastapi.responses import StreamingResponse
from app.services import ChatControllerServices

ChatRouter = APIRouter()

chatController = ChatControllerServices()


@ChatRouter.post("/chat")
async def chat(request: ChatRequestModel) -> StreamingResponse:
    return await chatController.Chat(request)
