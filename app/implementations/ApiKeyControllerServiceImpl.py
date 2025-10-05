from abc import ABC, abstractmethod
from app.models import (
    GenerateApiKeyResponseModel,
    HandleContextKeyGenerationRequestModel,
)


class HandleKeyInterfaceImpl(ABC):

    @abstractmethod
    def GenerateSalt(self) -> bytes:
        pass

    @abstractmethod
    def DeriveKeyHash(self, key: str, salt: bytes) -> str:
        pass

    @abstractmethod
    def GenerateKey(self, length: int = 64) -> GenerateApiKeyResponseModel:
        pass

    @abstractmethod
    def ValidateKey(self, key: str, storedHash: str, storedSalt: bytes) -> bool:
        pass


class ApiKeyControllerServiceImpl(ABC):

    @abstractmethod
    def HandleContextKeyGeneration(
        self, request: HandleContextKeyGenerationRequestModel
    ) -> None:
        pass
