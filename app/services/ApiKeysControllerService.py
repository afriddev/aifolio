from app.implementations import ApiKeysControllerServiceImpl
from fastapi.responses import JSONResponse
from database import mongoClient
from app.models import UpdateApiKeyRequestModel, FileModel, GenerateApiKeyRequestModel
from app.utils import AppUtils, GENERATE_CONTENT_PROMPT
from fastapi.responses import JSONResponse
from services import DocServices
from uuid import uuid4
from app.schemas import ContextFileSchema
from app.schemas import ApiKeySchema
from services import ChatServices
from models import ChatMessageModel, ChatRequestModel

from enums import ChatMessageRoleEnum, CerebrasChatModelEnum
from bson.binary import Binary
import json
from typing import Any,cast


class ApiKeysControllerService(ApiKeysControllerServiceImpl):
    def __init__(self):
        self.db = mongoClient["aifolio"]
        self.appUtils = AppUtils()
        self.docService = DocServices()
        self.chatService = ChatServices()

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

    def UploadFile(self, request: FileModel) -> JSONResponse:
        try:
            fileId = uuid4()
            text, _ = self.docService.ExtractTextAndImagesFromPdf(request.data)
            tokensCount = self.appUtils.CountTokens(text)
            if tokensCount > 5000:
                return JSONResponse(
                    status_code=413,
                    content={
                        "data": "FILE_TOO_LARGE",
                    },
                )
            dbSchema = ContextFileSchema(
                content=text,
                name=request.name,
                mediaType=request.mediaType,
                size=request.size,
                id=str(fileId),
                data=request.data,
                tokensCount=tokensCount,
            )
            collection = self.db["contextFiles"]
            collection.insert_one(dbSchema.model_dump())

            return JSONResponse(
                status_code=413,
                content={
                    "data": "SUCCESS",
                },
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

    async def GenerateApiKey(self, request: GenerateApiKeyRequestModel) -> JSONResponse:

        apiKeyCollection = self.db["apiKeys"]

        if retryLimit >= 3:
            tempApiSchema = ApiKeySchema(
                id=keyId,
                chatId=chatId,
                key=keyDetails.key,
                hash=keyDetails.hash,
                salt=Binary(keyDetails.salt),
                name="",
                status="ERROR",
            )

            apiKeyCollection.update_one(
                {"chatId": tempApiSchema.chatId},
                {"$set": tempApiSchema.model_dump()},
                upsert=True,
            )
            return

        try:
            tempApiSchema = ApiKeySchema(
                id=keyId,
                chatId=chatId,
                key=keyDetails.key,
                hash=keyDetails.hash,
                salt=Binary(keyDetails.salt),
                name="",
                status="PENDING",
            )
            apiKeyCollection.update_one(
                {"chatId": tempApiSchema.chatId},
                {"$set": tempApiSchema.model_dump()},
                upsert=True,
            )
            messages.pop(0)
            messages.append(
                ChatMessageModel(
                    role=ChatMessageRoleEnum.SYSTEM,
                    content=GENERATE_CONTENT_PROMPT,
                )
            )
            response: Any = await self.chatService.Chat(
                modelParams=ChatRequestModel(
                    messages=messages,
                    maxCompletionTokens=8000,
                    model=CerebrasChatModelEnum.GPT_OSS_120B,
                    method="cerebras",
                    temperature=0.3,
                    topP=0.9,
                    stream=False,
                    responseFormat={
                        "type": "object",
                        "properties": {
                            "contentForRag": {"type": "string"},
                            "name": {"type": "string"},
                        },
                        "required": ["contentForRag", "name"],
                        "additionalProperties": False,
                    },
                )
            )
            chatResponse: dict[str, Any] = {}
            if response.content:
                try:
                    chatResponse = json.loads(response.content)
                except Exception as e:
                    time.sleep(3)
                    await self.GenerateChunkContent(
                        messages,
                        chatId=chatId,
                        keyDetails=keyDetails,
                        keyId=keyId,
                        retryLimit=retryLimit + 1,
                    )
            contentForRag = chatResponse.get("response", {}).get("contentForRag", "")
            name = chatResponse.get("response", {}).get("name", "")
            self.apiKeyService.HandleContextKeyGeneration(
                request=HandleContextKeyGenerationRequestModel(
                    keyId=keyId,
                    keyDetails=keyDetails,
                    chatId=chatId,
                    context=contentForRag,
                    name=name,
                )
            )

        except Exception as e:
            print(e)
            time.sleep(3)
            await self.GenerateChunkContent(
                messages,
                chatId=chatId,
                keyDetails=keyDetails,
                keyId=keyId,
                retryLimit=retryLimit + 1,
            )
