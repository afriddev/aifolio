from fastapi import APIRouter
from app.services import ApiKeysControllerService



ApiKeysRouter = APIRouter()
ApiKeyService = ApiKeysControllerService()


@ApiKeysRouter.get("/apikeys")
def getApiKeys():
    return ApiKeyService.GetAllApiKeys()    