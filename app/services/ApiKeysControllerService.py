from app.implementations import ApiKeysControllerServiceImpl
from fastapi.responses import JSONResponse
from database import mongoClient


class ApiKeysControllerService(ApiKeysControllerServiceImpl):
    def __init__(self):
        self.db = mongoClient["aifolio"]

    def GetAllApiKeys(self) -> JSONResponse:
        try:
            collection = self.db["apikeys"]
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
                        "createdAt": apiKey.get("createdAt", ""),
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
