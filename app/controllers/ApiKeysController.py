from fastapi import APIRouter




ApiKeysRouter = APIRouter()



@ApiKeysRouter.get("/apikeys")
def getApiKeys():
    return 