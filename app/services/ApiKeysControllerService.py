from app.implementations import ApiKeysControllerServiceImpl
from fastapi.responses import JSONResponse
from database import mongoClient
from app.models import UpdateApiKeyRequestModel


class ApiKeysControllerService(ApiKeysControllerServiceImpl):
    def __init__(self):
        self.db = mongoClient["aifolio"]

    def GetAllApiKeys(self) -> JSONResponse:
        try:
            collection = self.db["apiKeys"]
            apiKeys = list(collection.find({}).sort("createdAt", -1))
            tempAllApiKeys: list[dict[str, str]] = []
            for apiKey in apiKeys:
                tempAllApiKeys.append(
                    {
                        "id": apiKey.get("id", ""),
                        "name": apiKey.get("name", ""),
                        "key": apiKey.get("key", ""),
                        "status": apiKey.get("status", "PENDING"),
                        "disabled": apiKey.get("disabled", False),
                        "deleted": apiKey.get("deleted", False),
                        "createdAt": str(apiKey.get("createdAt", "")),
                    }
                )
            return JSONResponse(
                status_code=200,
                content={"data": "SUCCESS", "keys": tempAllApiKeys},
            )
        except Exception as e:
            print(e)
            return JSONResponse(
                status_code=500,
                content={
                    "data": "ERROR",
                    "error": str(e),
                },
            )

    def UpdateApiKey(self, request: UpdateApiKeyRequestModel) -> JSONResponse:
        try:
            collection = self.db["apiKeys"]
            if request.method == "DELETE":
                collection.update_one({"id": request.id}, {"$set": {"deleted": True}})
            elif request.method == "DISABLE":
                collection.update_one({"id": request.id}, {"$set": {"disabled": True}})
            elif request.method == "ENABLE":
                collection.update_one({"id": request.id}, {"$set": {"disabled": False}})
            return JSONResponse(
                status_code=200,
                content={"data": "SUCCESS"},
            )
        except Exception as e:
            print(e)
            return JSONResponse(
                status_code=500,
                content={
                    "data": "ERROR",
                    "error": str(e),
                },
            )
