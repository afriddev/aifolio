from app.implementations import ApiKeysControllerServiceImpl
from fastapi.responses import JSONResponse
from database import (
    dataFilesCollection,
    apiKeysCollection,
    singleApiKeyDataCollection,
    psqlDbClient,
)
from app.models import (
    UpdateApiKeyRequestModel,
    FileModel,
    GenerateApiKeyRequestModel,
)
from app.utils import AppUtils, GENERATE_CONTENT_PROMPT
from fastapi.responses import JSONResponse
from services import DocServices
from uuid import uuid4
from app.schemas import ApiKeyFileSchema
from app.schemas import ApiKeySchema, ApiKeyDataSchema
from services import (
    ChatServices,
    DocServices,
    ChunkServices,
    RagServices,
    EmbeddingService,
)
from models import (
    ChatMessageModel,
    ChatRequestModel,
    AllChunksWithQuestionsModel,
    EmbeddingRequestModel,
    EmbeddingDataModel,
)
from enums import ChatMessageRoleEnum, CerebrasChatModelEnum
from bson.binary import Binary
import json
from typing import Any
import time
from app.services.ApiKeyService import HandleKeyInterface
import asyncio
from app.WebSocketManager import webSocket
from datetime import datetime, timezone
import re


class ApiKeysControllerService(ApiKeysControllerServiceImpl):
    def __init__(self):
        self.appUtils = AppUtils()
        self.docService = DocServices()
        self.chatService = ChatServices()
        self.keyInterface = HandleKeyInterface()
        self.chunkServices = ChunkServices()
        self.ragServices = RagServices()
        self.embeddingService = EmbeddingService()
        self.maxContextTokens = 5000
        self.maxPagesLimit = 50
        self.minimumTokensPerPage = 50
        self.maxChunkEmbeddingBatchSize = 10
        self.maxQuestionsEmbeddingBatchSize = 20
        self.db = psqlDbClient

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
                        "methodType": apiKey.get("methodType", "CONTEXT"),
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
            text, _, pages = self.docService.ExtractTextAndImagesFromPdf(
                request.data, images=False
            )
            if pages > self.maxPagesLimit:
                return JSONResponse(
                    status_code=400,
                    content={
                        "data": "MAX_PAGE_LIMIT",
                    },
                )
            tokensCount = self.appUtils.CountTokens(text)
            print(tokensCount)
            if tokensCount / pages < self.minimumTokensPerPage:
                return JSONResponse(
                    status_code=400,
                    content={
                        "data": "PAGE_CONTENT_TOO_LOW",
                    },
                )

            tempApiKeyDataSchema = ApiKeyFileSchema(
                name=request.name,
                mediaType=request.mediaType,
                size=request.size,
                id=str(fileId),
                data=request.data,
                tokensCount=tokensCount,
                type="RAG" if tokensCount > self.maxContextTokens else "CONTEXT",
            )

            dataFilesCollection.insert_one(tempApiKeyDataSchema.model_dump())

            return JSONResponse(
                status_code=200,
                content={
                    "data": "SUCCESS",
                    "fileId": str(fileId),
                    "methodType": (
                        "RAG" if tokensCount > self.maxContextTokens else "CONTEXT"
                    ),
                },
            )

        except Exception as e:
            print(e)
            return JSONResponse(
                status_code=500,
                content={
                    "data": "FILE_UPLOAD_ERROR",
                },
            )

    def UploadImagesFromFile(self, text: str, images: list[str]) -> str:
        matchedIndex = re.findall(r"<<[Ii][Mm][Aa][Gg][Ee]-([0-9]+)>>", text)
        indeces = list(map(int, matchedIndex))
        for index in indeces:
            imageUrl = self.docService.UploadImageToFileServer(
                base64Str=images[index - 1],
                name=f"{self.chunkServices.GenerateShortId()}.png",
            )
            token = f"<<image-{index}>>"
            print(imageUrl)
            text = text.replace(
                token, f"![Image]({imageUrl})" if imageUrl is not None else ""
            )
        return text

    async def HandleSingleFileContextProcess(self, keyId: str, retryLimit: int) -> None:
        keyData = apiKeysCollection.find_one({"id": keyId})
        fileData = dataFilesCollection.find_one({"id": keyData.get("singleFileId")})
        fileUrl = self.docService.UploadImageToFileServer(
            fileData.get("data"), fileData.get("name")
        )

        if (fileUrl == None) or (fileUrl == ""):
            await self.HandleSendUpdateKeyDetailsWebSocket(keyId, "ERROR")
            return

        text, images, _ = self.docService.ExtractTextAndImagesFromPdf(
            fileData.get("data"), images=True
        )
        fileContent = (
            self.UploadImagesFromFile(text, images)
            + "\n\n"
            + f"[📎 View or Download File]({fileData.get('fileUrl', '')})"
        )

        if retryLimit >= 3:
            await self.HandleSendUpdateKeyDetailsWebSocket(keyId, "ERROR")
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
                    await self.HandleSingleFileContextProcess(keyId, 0)
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

            await self.HandleSendUpdateKeyDetailsWebSocket(keyId, "ACTIVE")
            return

        except Exception as e:
            print(e)
            time.sleep(60)
        await self.HandleSingleFileContextProcess(keyId, 0)

    async def HandleSendUpdateKeyDetailsWebSocket(
        self, keyId: str, status: str
    ) -> None:
        apiKeysCollection.update_one(
            {"id": keyId},
            {"$set": {"status": status}},
            upsert=True,
        )
        await webSocket.sendToUser(
            email="afridayan01@gmail.com",
            message=json.dumps(
                {
                    "type": "UPDATE_API_KEY",
                    "id": keyId,
                    "status": status,
                }
            ),
        )
        return

    async def ConvertTextsToEmbedding(
        self, text: list[str]
    ) -> list[EmbeddingDataModel] | None:
        try:
            tempEmbeddingResponse: Any = await self.embeddingService.Embed(
                request=EmbeddingRequestModel(
                    model="baai/bge-m3",
                    texts=text,
                    type="passage",
                )
            )
            return tempEmbeddingResponse.data
        except Exception as e:
            print(f"Error in ConvertTextsToEmbedding: {e}")
            return None

    async def HandleSingleFileRagProcess(self, keyId: str) -> None:
        keyData = apiKeysCollection.find_one({"id": keyId})
        fileData = dataFilesCollection.find_one({"id": keyData.get("singleFileId")})
        fileUrl = self.docService.UploadImageToFileServer(
            fileData.get("data"), fileData.get("name")
        )
        if (fileUrl == None) or (fileUrl == ""):
            await self.HandleSendUpdateKeyDetailsWebSocket(keyId, "ERROR")
            print(1)
            return

        tempQuestionsAndChunkResponse: AllChunksWithQuestionsModel | None = None
        if fileData.get("mediaType", "") == "application/pdf":
            tempQuestionsAndChunkResponse = (
                await self.ragServices.ExtractQuestionAndAnswersFromPdfFile(
                    file=fileData.get("data")
                )
            )

        if tempQuestionsAndChunkResponse is not None:
            tempAllChunks = tempQuestionsAndChunkResponse.chunks
            tempAllQuestions = tempQuestionsAndChunkResponse.questions

            for i in range(0, len(tempAllChunks), self.maxChunkEmbeddingBatchSize):
                tempChunkEmbeddings = await self.ConvertTextsToEmbedding(
                    text=[
                        chunk.text
                        for chunk in tempAllChunks[
                            i : i + self.maxChunkEmbeddingBatchSize
                        ]
                    ]
                )
                if tempChunkEmbeddings is None:
                    await self.HandleSendUpdateKeyDetailsWebSocket(keyId, "ERROR")
                    print(2)

                    return

                for j, chunk in enumerate(
                    tempAllChunks[i : i + self.maxChunkEmbeddingBatchSize]
                ):
                    chunk.embedding = tempChunkEmbeddings[j].embedding
            for i in range(
                0, len(tempAllQuestions), self.maxQuestionsEmbeddingBatchSize
            ):
                tempQuestionEmbeddings = await self.ConvertTextsToEmbedding(
                    text=[
                        question.text
                        for question in tempAllQuestions[
                            i : i + self.maxQuestionsEmbeddingBatchSize
                        ]
                    ]
                )
                if tempQuestionEmbeddings is None:
                    print(3)

                    await self.HandleSendUpdateKeyDetailsWebSocket(keyId, "ERROR")
                    return

                for j, question in enumerate(
                    tempAllQuestions[i : i + self.maxQuestionsEmbeddingBatchSize]
                ):
                    question.embedding = tempQuestionEmbeddings[j].embedding

            try:
                async with self.db.pool.acquire() as conn:
                    await conn.executemany(
                        "INSERT INTO chunks (id, text, embedding) VALUES ($1, $2, $3)",
                        [
                            (chunk.id, chunk.text, chunk.embedding)
                            for chunk in tempAllChunks
                        ],
                    )

                    await conn.executemany(
                        "INSERT INTO questions (id,chunk_id, text, embedding) VALUES ($1, $2, $3,$4)",
                        [
                            (
                                question.id,
                                question.chunkId,
                                question.text,
                                question.embedding,
                            )
                            for question in tempAllQuestions
                        ],
                    )
                    await self.HandleSendUpdateKeyDetailsWebSocket(keyId, "SUCCESS")
            except Exception as e:
                print(f"Error inserting into PostgreSQL: {e}")
                await self.HandleSendUpdateKeyDetailsWebSocket(keyId, "ERROR")
                return
        else:
            print(4)

            await self.HandleSendUpdateKeyDetailsWebSocket(keyId, "ERROR")
            return

    async def GenerateApiKey(self, request: GenerateApiKeyRequestModel) -> JSONResponse:
        if request.keyId is None:
            keyId = str(uuid4())
            tempPdfFileIds = request.pdfFileIds if request.pdfFileIds else None
            tempCsvFileIds = request.csvFileIds if request.csvFileIds else None
            tempTxtFileIds = request.txtFileIds if request.txtFileIds else None
            tempYtVideoFileIds = (
                request.ytVideoFileIds if request.ytVideoFileIds else None
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
                filesType=request.filesType,
                singleFileId=request.singleFileId,
                methodType=request.methodType,
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
                        "methodType": request.methodType,
                    }
                ),
            )
            apiKeysCollection.insert_one(tempApiSchema.model_dump())
            if request.singleFileId is not None and request.filesType == "SINGLE":
                if request.methodType == "CONTEXT":
                    asyncio.create_task(self.HandleSingleFileContextProcess(keyId, 0))
                elif request.methodType == "RAG":
                    asyncio.create_task(self.HandleSingleFileRagProcess(keyId))

            return JSONResponse(
                status_code=200,
                content={"data": "SUCCESS"},
            )

        elif request.keyId:
            await self.HandleSendUpdateKeyDetailsWebSocket(request.keyId, "PENDING")
            if request.singleFileId is not None and request.filesType == "SINGLE":
                keyId = request.keyId
                if request.methodType == "CONTEXT":
                    asyncio.create_task(self.HandleSingleFileContextProcess(keyId, 0))
                elif request.methodType == "RAG":
                    asyncio.create_task(self.HandleSingleFileRagProcess(keyId))

            return JSONResponse(
                status_code=200,
                content={"data": "SUCCESS"},
            )
        else:
            return JSONResponse(
                status_code=400,
                content={"data": "GENERATE_KEY_ERROR"},
            )
