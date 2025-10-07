from abc import ABC, abstractmethod
from fastapi.responses import JSONResponse
from app.models import UpdateApiKeyRequestModel


class ApiKeysControllerServiceImpl(ABC):

    @abstractmethod
    def GetAllApiKeys(self) -> JSONResponse:
        pass

    @abstractmethod
    def UpdateApiKey(self, request: UpdateApiKeyRequestModel) -> JSONResponse:
        pass
