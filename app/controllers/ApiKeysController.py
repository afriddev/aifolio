from fastapi import APIRouter
from app.services import ApiKeysControllerService
from app.models import UpdateApiKeyRequestModel


ApiKeysRouter = APIRouter()
ApiKeyService = ApiKeysControllerService()


@ApiKeysRouter.get("/apikeys")
def getApiKeys():
    return ApiKeyService.GetAllApiKeys()


@ApiKeysRouter.get("/update/apikey")
def updateApiKey(request: UpdateApiKeyRequestModel):
    return ApiKeyService.UpdateApiKey(request)
