from app.implementations import ChatbotControllerImpl
import json
from app.models import (
    ChatbotRequestModel,
    GetApiKeyResponseModel,
    PreProcessUserQueryResponseModel,
)
from models import (
    ChatMessageModel,
    ChatRequestModel as ChatServiceRequestModel,
    EmbeddingDataModel,
    EmbeddingRequestModel,
)
from enums import ChatMessageRoleEnum, OpenaiChatModelsEnum
from services import ChatServices, EmbeddingService
from typing import Any, cast
from fastapi.responses import StreamingResponse
from app.utils import CHATBOT_DEMO_PROMPT, VALIDATE_USER_QUERY_PROMPT
from database import (
    cacheService,
    apiKeysCollection,
    singleApiKeyDataCollection,
    psqlDbClient,
)
from app.utils import AppUtils, SEARCH_RAG_QUERY, CHATBOT_RAG_DEMO_PROMPT
from app.services.ChatControllerServices import ChatControllerServices


class ChatbotControllerService(ChatbotControllerImpl):

    def __init__(self):
        self.chatService = ChatServices()
        self.appUtils = AppUtils()
        self.cache = cacheService
        self.db = psqlDbClient
        self.embeddingService = EmbeddingService()
        self.chatServices = ChatControllerServices()

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

    async def handlePreProcessUserQuery(
        self, query: str
    ) -> PreProcessUserQueryResponseModel:
        preProcessUserQueryMessages: list[ChatMessageModel] = [
            ChatMessageModel(
                role=ChatMessageRoleEnum.SYSTEM,
                content=VALIDATE_USER_QUERY_PROMPT,
            ),
            
            ChatMessageModel(
                role=ChatMessageRoleEnum.USER,
                content=query,
            ),
            
        ]
        tempResponse = await self.chatServices.PreProcessUserQuery(
            loopIndex=0, messages=preProcessUserQueryMessages
        )
        return tempResponse

    async def HandleChatbotRequest(
        self, request: ChatbotRequestModel
    ) -> StreamingResponse:

        try:
            preProcessUserQuery = await self.handlePreProcessUserQuery(
                query=request.query
            )

            keyData = self.GetApiKeyDataFromCache(request.apiKey)

            if keyData is None:
                return await self.appUtils.StreamErrorMessage(
                    "Authentication failed: The provided API key is invalid or not recognized."
                )
            elif keyData.status == "PENDING":
                return await self.appUtils.StreamErrorMessage(
                    "Your API key is still being activated. Please try again in a few minutes."
                )
            elif keyData.status == "DISABLED":
                return await self.appUtils.StreamErrorMessage(
                    "Access denied: This API key has been disabled. Contact support if you believe this is a mistake."
                )
            elif keyData.status == "ERROR":
                return await self.appUtils.StreamErrorMessage(
                    "The API key is in an error state due to a configuration or system issue. Please reach out to support for assistance."
                )

            if preProcessUserQuery.type == "ABUSE_LANG_ERROR":
                return await self.appUtils.StreamErrorMessage(
                    "Your message contains inappropriate or abusive language. Please modify your query and try again."
                )
            elif preProcessUserQuery.type == "CONTACT_INFO_ERROR":
                return await self.appUtils.StreamErrorMessage(
                    "Your message contains personal or sensitive information. Please remove such details and try again."
                )

            tempContextData = keyData.data if keyData.data is not None else ""
            searchResults: list[str] = []

            if keyData.methodType == "RAG" and preProcessUserQuery.type != "PREVIOUS":
                print(preProcessUserQuery.cleanQuery)
                queryVector = await self.ConvertTextsToEmbedding([preProcessUserQuery.cleanQuery])
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

            chatMessages: list[ChatMessageModel] = [
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
            ]
            if keyData.methodType == "CONTEXT":
                chatMessages.insert(
                    0,
                    ChatMessageModel(
                        role=ChatMessageRoleEnum.SYSTEM,
                        content=CHATBOT_DEMO_PROMPT.replace(
                            "{INTERNAL_CONTEXT}", tempContextData
                        ),
                    ),
                )

            elif keyData.methodType == "RAG" and preProcessUserQuery.type != "PREVIOUS":
                chatMessages.insert(
                    0,
                    ChatMessageModel(
                        role=ChatMessageRoleEnum.SYSTEM,
                        content=CHATBOT_RAG_DEMO_PROMPT,
                    ),
                )
                chatMessages.append(
                    ChatMessageModel(
                        role=ChatMessageRoleEnum.SYSTEM,
                        content=f"#Top results fetched from RAG Search -> { json.dumps(searchResults, indent=2)}",
                    )
                )
            chatMessages.append(
                ChatMessageModel(
                    role=ChatMessageRoleEnum.USER,
                    content=(request.query),
                ),
            )

            response: Any = await self.chatService.Chat(
                modelParams=ChatServiceRequestModel(
                    messages=chatMessages,
                    maxCompletionTokens=2000,
                    model=OpenaiChatModelsEnum.QWEN_NEXT_80B_250K_INSTRUCT,
                    method="openai",
                    temperature=0.2,
                    topP=0.95,
                    stream=True,
                    messageId=request.messageId,
                )
            )
            return response

        except Exception as e:
            print(f"Error occurred while handling chatbot request: {e}")
            return StreamingResponse(content=iter([]))
