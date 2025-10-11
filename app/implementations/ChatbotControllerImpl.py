from abc import ABC, abstractmethod
from app.models import ChatbotRequestModel, GetApiKeyResponseModel
from fastapi.responses import StreamingResponse


class ChatbotControllerImpl(ABC):

    @abstractmethod
    def GetApiKeyData(self, key: str) -> GetApiKeyResponseModel | None:
        pass

    @abstractmethod
    def GetApiKeyDataFromCache(self, key: str) -> GetApiKeyResponseModel | None:
        pass

    @abstractmethod
    async def HandleChatbotRequest(
        self, request: ChatbotRequestModel
    ) -> StreamingResponse:
        pass
