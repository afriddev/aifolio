from abc import ABC, abstractmethod
from fastapi.responses import JSONResponse


class ApiKeysControllerServiceImpl(ABC):

    @abstractmethod
    def GetAllApiKeys(self) -> JSONResponse:
        pass
