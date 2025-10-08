from abc import ABC, abstractmethod


class ChatbotControllerImpl(ABC):

    @abstractmethod
    def GetApiKeyData(self, key: str) -> str | None:
        pass

    @abstractmethod
    def CheckApiKey(self, key: str) -> bool:
        pass
