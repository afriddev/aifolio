from app.implementations import ApiKeysControllerServiceImpl
from fastapi.responses import JSONResponse
from database import dataFilesCollection, apiKeysCollection, singleApiKeyDataCollection
from app.models import UpdateApiKeyRequestModel, FileModel, GenerateApiKeyRequestModel
from app.utils import AppUtils, GENERATE_CONTENT_PROMPT
from fastapi.responses import JSONResponse
from services import DocServices
from uuid import uuid4
from app.schemas import ApiKeyFileSchema
from app.schemas import ApiKeySchema, ApiKeyDataSchema
from services import ChatServices, DocServices
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
        self.appUtils = AppUtils()
        self.docService = DocServices()
        self.chatService = ChatServices()
        self.keyInterface = HandleKeyInterface()
        self.docServices = DocServices()
        self.maxContextTokens = 6500
        self.maxPagesLimit = 50
        self.minimumTokensPerPage = 50

    def GetAllApiKeys(self) -> JSONResponse:
        try:
            apiKeys = list(
                apiKeysCollection.find({"deleted": False}).sort("createdAt", -1)
            )
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
                content={"data": "SERVER_ERROR"},
            )

    def UpdateApiKey(self, request: UpdateApiKeyRequestModel) -> JSONResponse:
        try:
            if request.method == "DELETE":
                apiKeysCollection.update_one(
                    {"id": request.id}, {"$set": {"deleted": True}}
                )
            elif request.method == "DISABLE":

                apiKeysCollection.update_one(
                    {"id": request.id},
                    {"$set": {"disabled": True, "status": "DISABLED"}},
                )
            elif request.method == "ENABLE":
                apiKeysCollection.update_one(
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
            text, _, pages = self.docService.ExtractTextAndImagesFromPdf(request.data)
            if pages > self.maxPagesLimit:
                return JSONResponse(
                    status_code=400,
                    content={
                        "data": "MAX_PAGE_LIMIT",
                    },
                )
            tokensCount = self.appUtils.CountTokens(text)
            if tokensCount / pages < self.minimumTokensPerPage:
                return JSONResponse(
                    status_code=400,
                    content={
                        "data": "PAGE_CONTENT_TOO_LOW",
                    },
                )

            fileUrl = self.docServices.UploadImageToFileServer(
                request.data, request.name
            )

            if (fileUrl == None) or (fileUrl == ""):
                return JSONResponse(
                    status_code=500,
                    content={
                        "data": "FILE_UPLOAD_ERROR",
                    },
                )
            dbSchema = ApiKeyFileSchema(
                content=text,
                name=request.name,
                mediaType=request.mediaType,
                size=request.size,
                id=str(fileId),
                data=request.data,
                tokensCount=tokensCount,
                fileUrl=fileUrl,
                type="RAG" if tokensCount > self.maxContextTokens else "CONTEXT",
            )

            dataFilesCollection.insert_one(dbSchema.model_dump())

            return JSONResponse(
                status_code=200,
                content={"data": "SUCCESS", "fileId": str(fileId)},
            )

        except Exception as e:
            print(e)
            return JSONResponse(
                status_code=500,
                content={
                    "data": "FILE_UPLOAD_ERROR",
                },
            )

    async def HandleFileProcessing(self, keyId: str, retryLimit: int) -> None:
        fileId = apiKeysCollection.find_one({"id": keyId}).get("fileId")
        fileContent = self.GetFileContent(fileId)

        if retryLimit >= 3:
            apiKeysCollection.update_one(
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
                    model=CerebrasChatModelEnum.QWEN_235B_INSTRUCT,
                    method="cerebras",
                    temperature=0.3,
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

            tempContentId = str(uuid4())
            apiKeyDataSchema = ApiKeyDataSchema(
                apiKeyId=keyId,
                data=content,
                id=tempContentId,
            )
            singleApiKeyDataCollection.insert_one(apiKeyDataSchema.model_dump())
            apiKeysCollection.update_one(
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
        fileData = dataFilesCollection.find_one({"id": fileId})
        if fileData:
            return (
                fileData.get("content", "")
                + "\n\n"
                + f"[📎 View or Download File]({fileData.get('fileUrl', '')})"
            )
        return ""

    async def GenerateApiKey(self, request: GenerateApiKeyRequestModel) -> JSONResponse:
        if request.keyId is None:
            keyId = str(uuid4())
            tempPdfFileIds = request.pdfFileIds if request.pdfFileIds else []
            tempCsvFileIds = request.csvFileIds if request.csvFileIds else []
            tempTxtFileIds = request.txtFileIds if request.txtFileIds else []
            tempYtVideoFileIds = (
                request.ytVideoFileIds if request.ytVideoFileIds else []
            )
            keyDetails = self.keyInterface.GenerateKey()
            createdAt = datetime.now(timezone.utc)

            tempApiSchema = ApiKeySchema(
                id=keyId,
                pdfFileIds=tempPdfFileIds,
                csvFileIds=tempCsvFileIds,
                txtFileIds=tempTxtFileIds,
                ytVideoFileIds=tempYtVideoFileIds,
                key=keyDetails.key,
                hash=keyDetails.hash,
                salt=Binary(keyDetails.salt),
                name=request.name,
                status="PENDING",
                createdAt=createdAt,
                type="SINGLE",
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
            apiKeysCollection.insert_one(tempApiSchema.model_dump())
            asyncio.create_task(self.HandleFileProcessing(keyId, 0))
            return JSONResponse(
                status_code=200,
                content={"data": "SUCCESS"},
            )

        elif request.keyId:
            keyId = request.keyId
            asyncio.create_task(self.HandleFileProcessing(keyId, 0))
            return JSONResponse(
                status_code=200,
                content={"data": "SUCCESS"},
            )
        else:
            return JSONResponse(
                status_code=400,
                content={"data": "GENERATE_KEY_ERROR"},
            )
