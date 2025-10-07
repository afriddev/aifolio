from abc import ABC, abstractmethod
from app.models import ChatRequestModel, FileModel, GenerateApiKeyResponseModel
from fastapi.responses import StreamingResponse, JSONResponse
from models import ChatMessageModel
from app.schemas import ChatMessageSchema, ChatSchema


class ChatControllerServiceImpl(ABC):
    @abstractmethod
    async def GenerateChatSummary(
        self,
        query: str,
        id: str,
        emailId: str,
        messagesLength: int,
        retryLimit: int,
    ) -> None:
        pass

    @abstractmethod
    async def Chat(self, request: ChatRequestModel) -> StreamingResponse:
        pass

    @abstractmethod
    def SaveChatMessage(self, request: ChatMessageSchema, retryLimit: int) -> None:
        pass

    @abstractmethod
    def SaveChat(self, request: ChatSchema, retryLimit: int) -> None:
        pass



    @abstractmethod
    def GetAllChats(self) -> JSONResponse:
        pass

    @abstractmethod
    def getChatHistory(self, id: str) -> JSONResponse:
        pass

    @abstractmethod
    async def UploadFile(self, request: FileModel, retryLimit: int) -> JSONResponse:
        pass

    @abstractmethod
    async def GenerateChunkContent(
        self,
        messages: list[ChatMessageModel],
        keyDetails: GenerateApiKeyResponseModel,
        chatId: str,
        keyId: str,
        retryLimit: int,
    ) -> None:
        pass
