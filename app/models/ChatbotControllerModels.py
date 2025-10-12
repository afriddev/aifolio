from app.models.ChatControllerModels import ChatRequestModel
from pydantic import BaseModel


class ChatbotRequestModel(ChatRequestModel):
    apiKey: str


class GetApiKeyResponseModel(BaseModel):
    status: str | None = None
    data: str | None = None
    methodType: str = "CONTEXT"
