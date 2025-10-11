from app.implementations import ChatbotControllerImpl
import json
from app.models import ChatbotRequestModel, GetApiKeyResponseModel
from models import ChatMessageModel, ChatRequestModel as ChatServiceRequestModel
from enums import ChatMessageRoleEnum, OpenaiChatModelsEnum
from services import ChatServices
from typing import Any
from fastapi.responses import StreamingResponse
from app.utils import CHATBOT_DEMO_PROMPT
from database import mongoClient, cacheService
from app.utils import AppUtils


class ChatbotControllerService(ChatbotControllerImpl):

    def __init__(self):
        self.chatService = ChatServices()
        self.appUtils = AppUtils()
        self.db = mongoClient["aifolio"]
        self.cache = cacheService

    def GetApiKeyData(self, key: str) -> GetApiKeyResponseModel | None:
        tempApiKeyData = self.db["apiKeys"].find_one({"key": key})
        tempApiKeyId = tempApiKeyData.get("id") if tempApiKeyData.get("id") else None
        # Key Details
        tempKeyStatus = (
            tempApiKeyData.get("status") if tempApiKeyData.get("status") else None
        )
        tempKeyData = None

        if tempApiKeyId is None:
            return None
        elif tempKeyStatus != "ACTIVE":
            return GetApiKeyResponseModel(status=tempKeyStatus, data=tempKeyData)

        else:
            tempKeyDataDetails = self.db["apiKeyData"].find_one({"apiKeyId": tempApiKeyId})
            tempKeyData = (
                tempKeyDataDetails.get("data")
                if tempKeyDataDetails.get("data")
                else None
            )

        return GetApiKeyResponseModel(status=tempKeyStatus, data=tempKeyData)

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
                if keyData.status == "ACTIVE" and keyData.data:
                    self.cache.SetKeyDetails(key, json.dumps(keyData.model_dump()))
                    return keyData
                else:
                    return GetApiKeyResponseModel(status="ERROR", data=None)

    async def HandleChatbotRequest(
        self, request: ChatbotRequestModel
    ) -> StreamingResponse:

        try:
            keyData = self.GetApiKeyDataFromCache(request.apiKey)
            print(keyData)
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

            chatMessages: list[ChatMessageModel] = [
                ChatMessageModel(
                    role=ChatMessageRoleEnum.SYSTEM,
                    content=CHATBOT_DEMO_PROMPT,
                ),
                ChatMessageModel(
                    role=ChatMessageRoleEnum.SYSTEM,
                    content=keyData.data if keyData.data is not None else "",
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
                    maxCompletionTokens=3000,
                    model=OpenaiChatModelsEnum.MISTRAL_NEMOTRON_240K,
                    method="openai",
                    temperature=0.5,
                    topP=1.0,
                    stream=True,
                    messageId=request.messageId,
                )
            )
            return response

        except Exception as e:
            print(e)
            return StreamingResponse(content=iter([]))
