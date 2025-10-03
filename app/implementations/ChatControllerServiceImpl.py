from abc import ABC, abstractmethod
from app.models import ChatRequestModel, FileModel
from fastapi.responses import StreamingResponse, JSONResponse
from models import ChatMessageModel
from app.schemas import ChatMessageSchema, ChatSchema


class ChatControllerServiceImpl(ABC):

    @abstractmethod
    async def Chat(self, request: ChatRequestModel) -> StreamingResponse:
        pass

    @abstractmethod
    async def UploadFile(self, request: FileModel, retryLimit: int) -> JSONResponse:
        pass

    @abstractmethod
    def GetFileContent(self, fileId: str) -> str:
        pass

    @abstractmethod
    async def GenerateChatSummary(
        self, query: str, id: str, emailId: str, retryLimit: int
    ) -> None:
        pass

    @abstractmethod
    def SaveChat(self, request: ChatSchema, retryLimit: int) -> None:
        pass

    @abstractmethod
    def SaveChatMessage(self, request: ChatMessageSchema, retryLimit: int) -> None:
        pass

    @abstractmethod
    async def GenerateResumeContent(self, messages: list[ChatMessageModel]) -> None:
        pass
