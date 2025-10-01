from abc import ABC, abstractmethod
from app.models import ChatRequestModel
from fastapi.responses import StreamingResponse


class ChatControllerServiceImpl(ABC):

    @abstractmethod
    async def Chat(self, request: ChatRequestModel) -> StreamingResponse:
        pass
