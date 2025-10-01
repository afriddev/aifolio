from abc import ABC, abstractmethod
from typing import Any
from fastapi.responses import StreamingResponse
from models import ChatResponseModel,ChatRequestModel


class ChatServicesImpl(ABC):

    @abstractmethod
    async def OpenaiChat(self, modelParams: ChatRequestModel) -> Any:
        pass

    @abstractmethod
    async def Chat(
        self, modelParams: ChatRequestModel
    ) -> ChatResponseModel | StreamingResponse:
        pass
