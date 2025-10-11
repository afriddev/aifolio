from abc import ABC, abstractmethod
from fastapi.responses import StreamingResponse

class AppUtilsImpl(ABC):
    
    @abstractmethod
    def CountTokens(self, text: str) -> int:
        pass

    @abstractmethod
    async def StreamErrorMessage(self, error: str) -> StreamingResponse:
        pass
