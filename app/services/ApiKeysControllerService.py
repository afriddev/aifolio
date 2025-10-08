from app.implementations import ApiKeysControllerServiceImpl
from fastapi.responses import JSONResponse
from database import mongoClient
from app.models import UpdateApiKeyRequestModel, FileModel, GenerateApiKeyRequestModel
from app.utils import AppUtils, GENERATE_CONTENT_PROMPT
from fastapi.responses import JSONResponse
from services import DocServices
from uuid import uuid4
from app.schemas import ContextFileSchema
from app.schemas import ApiKeySchema, ApiKeyDataSchema
from services import ChatServices
from models import ChatMessageModel, ChatRequestModel

from enums import ChatMessageRoleEnum, CerebrasChatModelEnum
from bson.binary import Binary
import json
from typing import Any
import time
from app.services.ApiKeyService import HandleKeyInterface
import asyncio
from app.WebSocketManager import webSocket
from datetime import datetime, timezone


class ApiKeysControllerService(ApiKeysControllerServiceImpl):
    def __init__(self):
        self.db = mongoClient["aifolio"]
        self.appUtils = AppUtils()
        self.docService = DocServices()
        self.chatService = ChatServices()
        self.keyInterface = HandleKeyInterface()

    def GetAllApiKeys(self) -> JSONResponse:
        try:
            collection = self.db["apiKeys"]
            apiKeys = list(collection.find({"deleted": False}).sort("createdAt", -1))
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
                collection.update_one(
                    {"id": request.id},
                    {"$set": {"disabled": True, "status": "DISABLED"}},
                )
            elif request.method == "ENABLE":
                collection.update_one(
                    {"id": request.id},
                    {"$set": {"disabled": False, "status": "ACTIVE"}},
                )
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
                status_code=200,
                content={"data": "SUCCESS", "fileId": str(fileId)},
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

    async def HandleFileProcessing(self, keyId: str, retryLimit: int) -> None:
        apiKeyCollection = self.db["apiKeys"]
        fileId = apiKeyCollection.find_one({"id": keyId}).get("fileId")

        fileContent = self.GetFileContent(fileId)

        if retryLimit >= 3:
            apiKeyCollection.update_one(
                {"id": keyId},
                {"$set": {"status": "ERROR"}},
                upsert=True,
            )
            await webSocket.sendToUser(
                email="afridayan01@gmail.com",
                message=json.dumps(
                    {
                        "type": "UPDATE_API_KEY",
                        "id": keyId,
                        "status": "ERROR",
                    }
                ),
            )
            return

        try:
            response: Any = await self.chatService.Chat(
                modelParams=ChatRequestModel(
                    messages=[
                        ChatMessageModel(
                            role=ChatMessageRoleEnum.SYSTEM,
                            content=GENERATE_CONTENT_PROMPT,
                        ),
                        ChatMessageModel(
                            role=ChatMessageRoleEnum.USER, content=fileContent
                        ),
                    ],
                    maxCompletionTokens=8000,
                    model=CerebrasChatModelEnum.GPT_OSS_120B,
                    method="cerebras",
                    temperature=0.1,
                    topP=0.9,
                    stream=False,
                    responseFormat={
                        "type": "object",
                        "properties": {
                            "content": {"type": "string"},
                        },
                        "required": ["content"],
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
                    await self.HandleFileProcessing(keyId, 0)
            content = chatResponse.get("response", {}).get("content", "")
            apiKeyDataSchema = ApiKeyDataSchema(
                apiKeyId=keyId,
                data=content,
                id=str(uuid4()),
            )
            apiKeyDataCollection = self.db["apiKeyData"]
            apiKeyDataCollection.insert_one(apiKeyDataSchema.model_dump())
            apiKeyCollection.update_one(
                {"id": keyId},
                {"$set": {"status": "ACTIVE"}},
                upsert=True,
            )
            await webSocket.sendToUser(
                email="afridayan01@gmail.com",
                message=json.dumps(
                    {
                        "type": "UPDATE_API_KEY",
                        "id": keyId,
                        "status": "ACTIVE",
                    }
                ),
            )
            return

        except Exception as e:
            print(e)
            time.sleep(60)
        await self.HandleFileProcessing(keyId, 0)

    def GetFileContent(self, fileId: str) -> str:
        collection = self.db["contextFiles"]
        fileData = collection.find_one({"id": fileId})
        if fileData:
            return fileData.get("content", "")
        return ""

    def GetApiKeyData(self, id: str) -> JSONResponse:
        try:
            apiKeyCollection = self.db["apiKeys"]
            fileId = apiKeyCollection.find_one({"id": id}).get("fileId")
            fileContent = self.GetFileContent(fileId)

            return JSONResponse(
                status_code=200,
                content={"data": "SUCCESS", "keyData": fileContent},
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

        if request.keyId is None and request.fileId is not None:
            keyId = str(uuid4())
            fileId = request.fileId
            keyDetails = self.keyInterface.GenerateKey()
            createdAt = datetime.now(timezone.utc)

            tempApiSchema = ApiKeySchema(
                id=keyId,
                fileId=fileId,
                key=keyDetails.key,
                hash=keyDetails.hash,
                salt=Binary(keyDetails.salt),
                name=request.name,
                status="PENDING",
                createdAt=createdAt,
            )
            await webSocket.sendToUser(
                email="afridayan01@gmail.com",
                message=json.dumps(
                    {
                        "type": "ADD_API_KEY",
                        "key": keyDetails.key,
                        "id": keyId,
                        "name": request.name,
                        "status": "PENDING",
                        "createdAt": str(createdAt),
                        "disabled": False,
                        "deleted": False,
                    }
                ),
            )
            collection = self.db["apiKeys"]
            collection.insert_one(tempApiSchema.model_dump())
            asyncio.create_task(self.HandleFileProcessing(keyId, 0))
            return JSONResponse(
                status_code=200,
                content={"data": "SUCCESS"},
            )

        elif request.keyId is not None and request.fileId is None:
            keyId = request.keyId
            asyncio.create_task(self.HandleFileProcessing(keyId, 0))
            return JSONResponse(
                status_code=200,
                content={"data": "SUCCESS"},
            )
        else:
            return JSONResponse(
                status_code=400,
                content={"data": "ERROR"},
            )
