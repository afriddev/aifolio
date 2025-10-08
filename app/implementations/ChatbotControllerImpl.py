from abc import ABC, abstractmethod


class ChatbotControllerImpl(ABC):

    @abstractmethod
    def GetApiKeyStatus(self, keyId: str) -> str:
        pass

    @abstractmethod
    def GetApiKeyId(self, key: str) -> str | None:
        pass

    @abstractmethod
    def GetApiKeyData(self, keyId: str) -> str:
        pass
