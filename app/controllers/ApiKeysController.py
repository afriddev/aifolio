from fastapi import APIRouter
from app.services import ApiKeysControllerService
from app.models import UpdateApiKeyRequestModel
from app.models import FileModel,GenerateApiKeyRequestModel

ApiKeysRouter = APIRouter()
ApiKeyService = ApiKeysControllerService()


@ApiKeysRouter.get("/apikeys/all")
def getApiKeys():
    return ApiKeyService.GetAllApiKeys()


@ApiKeysRouter.post("/apikeys/update/apikey")
def updateApiKey(request: UpdateApiKeyRequestModel):
    return ApiKeyService.UpdateApiKey(request)


@ApiKeysRouter.post("/apikeys/upload/file")
def UploadFile(request: FileModel): 
    return ApiKeyService.UploadFile(request)

@ApiKeysRouter.post("/apikeys/generate/apikey")
async def generateApiKey(request:GenerateApiKeyRequestModel):
    return await ApiKeyService.GenerateApiKey(request)

