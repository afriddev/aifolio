from abc import ABC, abstractmethod
from fastapi.responses import JSONResponse
from app.models import UpdateApiKeyRequestModel, FileModel, GenerateApiKeyRequestModel


class ApiKeysControllerServiceImpl(ABC):

    @abstractmethod
    def GetAllApiKeys(self) -> JSONResponse:
        pass

    @abstractmethod
    def UpdateApiKey(self, request: UpdateApiKeyRequestModel) -> JSONResponse:
        pass

    @abstractmethod
    def UploadFile(self, request: FileModel) -> JSONResponse:
        pass

    @abstractmethod
    def UploadImagesFromFile(self, text: str, images: list[str]) -> str:
        pass

    @abstractmethod
    async def HandleSingleFileContextProcess(self, keyId: str, retryLimit: int) -> None:
        pass

    @abstractmethod
    async def GenerateApiKey(self, request: GenerateApiKeyRequestModel) -> JSONResponse:
        pass
