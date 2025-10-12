from app.implementations import ChatbotControllerImpl
import json
from app.models import ChatbotRequestModel, GetApiKeyResponseModel
from models import (
    ChatMessageModel,
    ChatRequestModel as ChatServiceRequestModel,
    EmbeddingDataModel,
    EmbeddingRequestModel,
    RerankRequestModel,
)
from enums import ChatMessageRoleEnum, OpenaiChatModelsEnum
from services import ChatServices, EmbeddingService
from typing import Any, cast
from fastapi.responses import StreamingResponse
from app.utils import CHATBOT_DEMO_PROMPT
from database import (
    cacheService,
    apiKeysCollection,
    singleApiKeyDataCollection,
    psqlDbClient,
)
from app.utils import AppUtils, SEARCH_RAG_QUERY, CHATBOT_RAG_DEMO_PROMPT


class ChatbotControllerService(ChatbotControllerImpl):

    def __init__(self):
        self.chatService = ChatServices()
        self.appUtils = AppUtils()
        self.cache = cacheService
        self.db = psqlDbClient
        self.embeddingService = EmbeddingService()

    def GetApiKeyData(self, key: str) -> GetApiKeyResponseModel | None:
        tempApiKeyData = apiKeysCollection.find_one({"key": key})
        tempApiKeyId = tempApiKeyData.get("id") if tempApiKeyData.get("id") else None
        tempKeyStatus = (
            tempApiKeyData.get("status") if tempApiKeyData.get("status") else None
        )
        tempApiKeyMethod = (
            tempApiKeyData.get("methodType")
            if tempApiKeyData.get("methodType")
            else "CONTEXT"
        )
        tempKeyData = None

        if tempApiKeyId is None:
            return None
        elif tempKeyStatus != "ACTIVE":
            return GetApiKeyResponseModel(
                status=tempKeyStatus, data=tempKeyData, methodType=tempApiKeyMethod
            )

        elif tempApiKeyMethod == "CONTEXT" and tempKeyStatus == "ACTIVE":
            tempKeyDataDetails = singleApiKeyDataCollection.find_one(
                {"apiKeyId": tempApiKeyId}
            )
            tempKeyData = (
                tempKeyDataDetails.get("data")
                if tempKeyDataDetails.get("data")
                else None
            )

        return GetApiKeyResponseModel(
            status=tempKeyStatus, data=tempKeyData, methodType=tempApiKeyMethod
        )

    def GetApiKeyDataFromCache(self, key: str) -> GetApiKeyResponseModel | None:
        cachedData = self.cache.GetKeyDetails(key)
        if cachedData:
            return GetApiKeyResponseModel(**json.loads(cachedData))
        else:
            keyData = self.GetApiKeyData(key)
            if keyData is None:
                return None
            elif keyData.status == "PENDING":
                return GetApiKeyResponseModel(status="PENDING", data=None)

            elif keyData.status == "DISABLED":
                return GetApiKeyResponseModel(status="DISABLED", data=None)
            else:
                if keyData.status == "ACTIVE":
                    self.cache.SetKeyDetails(key, json.dumps(keyData.model_dump()))
                    return keyData
                else:
                    return GetApiKeyResponseModel(status="ERROR", data=None)

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

    async def HandleChatbotRequest(
        self, request: ChatbotRequestModel
    ) -> StreamingResponse:

        try:
            keyData = self.GetApiKeyDataFromCache(request.apiKey)

            if keyData is None:
                return await self.appUtils.StreamErrorMessage(
                    "Authentication failed: The provided API key is invalid or not recognized."
                )

            if keyData.status == "PENDING":
                return await self.appUtils.StreamErrorMessage(
                    "Your API key is still being activated. Please try again in a few minutes."
                )

            if keyData.status == "DISABLED":
                return await self.appUtils.StreamErrorMessage(
                    "Access denied: This API key has been disabled. Contact support if you believe this is a mistake."
                )

            if keyData.status == "ERROR":
                return await self.appUtils.StreamErrorMessage(
                    "The API key is in an error state due to a configuration or system issue. Please reach out to support for assistance."
                )

            tempContextData = keyData.data if keyData.data is not None else ""
            searchResults: list[str] = []
            topDocs: list[str] = []

            if keyData.methodType == "RAG":
                queryVector = await self.ConvertTextsToEmbedding([request.query])
                if queryVector is None:
                    raise Exception("Failed to generate embedding for the query.")
                async with self.db.pool.acquire() as conn:
                    await conn.set_type_codec(
                        "jsonb",
                        encoder=json.dumps,
                        decoder=json.loads,
                        schema="pg_catalog",
                    )
                    rows = await conn.fetch(
                        SEARCH_RAG_QUERY, cast(Any, queryVector)[0].embedding, 5
                    )

                    for row in rows:
                        question = row.get("question_text", "")
                        answer = row.get("chunk_text", "")
                        searchResults.append(
                            f"For this question : {question} Answer is {answer}"
                        )
            #     topRerankedDocs = await self.embeddingService.RerankDocs(
            #         request=RerankRequestModel(
            #             query=request.query,
            #             topN=5,
            #             docs=searchResults,
            #         )
            #     )
            #     topDocs: list[str] = [
            #         cast(Any, doc.doc or "") for doc in topRerankedDocs.results
            #     ]
            # print(topDocs)

            chatMessages: list[ChatMessageModel] = [
                (
                    ChatMessageModel(
                        role=ChatMessageRoleEnum.SYSTEM,
                        content=CHATBOT_DEMO_PROMPT.replace(
                            "{INTERNAL_CONTEXT}", tempContextData
                        ),
                    )
                    if keyData.methodType == "CONTEXT"
                    else ChatMessageModel(
                        role=ChatMessageRoleEnum.SYSTEM,
                        content=CHATBOT_RAG_DEMO_PROMPT.replace(
                            "{TOP_DOCS}", json.dumps(searchResults, indent=2)
                        ),
                    )
                ),
                *(
                    ChatMessageModel(
                        role=(
                            ChatMessageRoleEnum.USER
                            if msg.role == "user"
                            else ChatMessageRoleEnum.ASSISTANT
                        ),
                        content=msg.content,
                    )
                    for msg in request.messages
                ),
                ChatMessageModel(
                    role=ChatMessageRoleEnum.USER,
                    content=(request.query),
                ),
            ]
            response: Any = await self.chatService.Chat(
                modelParams=ChatServiceRequestModel(
                    messages=chatMessages,
                    maxCompletionTokens=1000,
                    model=OpenaiChatModelsEnum.QWEN_NEXT_80B_250K_INSTRUCT,
                    method="openai",
                    temperature=0.9,
                    topP=1.0,
                    stream=True,
                    messageId=request.messageId,
                )
            )
            return response

        except Exception as e:
            print(f"Error occurred while handling chatbot request: {e}")
            return StreamingResponse(content=iter([]))
