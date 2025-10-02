from abc import ABC, abstractmethod
from app.models import ChatRequestModel,FileModel
from fastapi.responses import StreamingResponse


class ChatControllerServiceImpl(ABC):

    @abstractmethod
    async def Chat(self, request: ChatRequestModel) -> StreamingResponse:
        pass
    
    @abstractmethod
    async def UploadFile(self, request: FileModel) -> None:
        pass

