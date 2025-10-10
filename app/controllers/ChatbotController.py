from fastapi import APIRouter
from app.models import ChatbotRequestModel


ChatbotRouter = APIRouter()

from app.services import ChatbotControllerService


chatBotController = ChatbotControllerService()


@ChatbotRouter.post("/chat/demo")
async def handleChatbotDemoRequest(request: ChatbotRequestModel):
    return await chatBotController.HandleChatbotRequest(request)
