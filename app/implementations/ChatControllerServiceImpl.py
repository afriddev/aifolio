from abc import ABC, abstractmethod
from app.models import ChatRequestModel, FileModel
from fastapi.responses import StreamingResponse, JSONResponse
from models import ChatMessageModel


class ChatControllerServiceImpl(ABC):

    @abstractmethod
    async def Chat(self, request: ChatRequestModel) -> StreamingResponse:
        pass

    @abstractmethod
    async def UploadFile(self, request: FileModel) -> JSONResponse:
        pass
    
    @abstractmethod
    def GetFileContent(self, fileId: str) -> str:
        pass


    @abstractmethod
    async def GenerateResumeContent(
        self, messages: list[ChatMessageModel]
    ) -> JSONResponse:
        pass
