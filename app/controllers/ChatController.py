from fastapi import APIRouter
from app.models import ChatRequestModel, FileModel, DeleteChatRequestModel
from fastapi.responses import StreamingResponse
from app.services import ChatControllerServices

ChatRouter = APIRouter()

chatService = ChatControllerServices()


@ChatRouter.post("/chat")
async def chat(request: ChatRequestModel) -> StreamingResponse:
    return await chatService.Chat(request)


@ChatRouter.post("/upload")
async def upload(request: FileModel):
    return await chatService.UploadFile(request)


@ChatRouter.get("/allchats")
async def allChats():
    return chatService.GetAllChats()


@ChatRouter.get("/chatistory/{id}")
async def chatHistory(id: str):
    return chatService.getChatHistory(id)


@ChatRouter.post("/deletechat")
async def deleteChat(request: DeleteChatRequestModel):
    return chatService.DeleteChat(request.id)
