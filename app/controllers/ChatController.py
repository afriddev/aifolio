from fastapi import APIRouter
from app.models import ChatRequestModel,FileModel
from fastapi.responses import StreamingResponse
from app.services import ChatControllerServices

ChatRouter = APIRouter()

chatService = ChatControllerServices()


@ChatRouter.post("/chat")
async def chat(request: ChatRequestModel) -> StreamingResponse:
    return await chatService.Chat(request)

@ChatRouter.post('/upload')
async def upload(request:FileModel):
    return await chatService.UploadFile(request)   