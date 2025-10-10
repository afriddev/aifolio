from app.implementations import ChatbotControllerImpl
from database import redisClient
import json
from app.models import ChatbotRequestModel
from models import ChatMessageModel, ChatRequestModel as ChatServiceRequestModel
from enums import ChatMessageRoleEnum, OpenaiChatModelsEnum
from services import ChatServices
from typing import Any, cast
from fastapi.responses import StreamingResponse
from app.utils import CHATBOT_DEMO_PROMPT


class ChatbotControllerService(ChatbotControllerImpl):

    def __init__(self):
        self.redisClient = redisClient
        self.chatService = ChatServices()

    def GetApiKeyId(self, key: str) -> str | None:
        tempKeyData = self.redisClient.getApiKeyId(key)
        print(tempKeyData)
        if tempKeyData is not None:
            tempKeyData = json.loads(tempKeyData)
            return tempKeyData["id"]
        return None

    def GetApiKeyStatus(self, keyId: str) -> str:
        tempKeyData = self.redisClient.getApiKeyValue(keyId)
        if tempKeyData is not None:
            tempKeyData = json.loads(tempKeyData)
            return tempKeyData["status"]
        return "NOT_FOUND"

    def GetApiKeyData(self, keyId: str) -> str:
        tempKeyData = self.redisClient.getApiKeyDataValue(keyId)
        if tempKeyData is not None:
            tempKeyData = json.loads(tempKeyData)
            return tempKeyData["data"]
        return "ERROR"

    async def HandleChatbotRequest(
        self, request: ChatbotRequestModel
    ) -> StreamingResponse:
        print("Hell Nah!")
        try:
            keyData = ""
            keyId = self.GetApiKeyId(request.apiKey)
            print("Hell Nah")

            if keyId is None:
                print(1)
                return StreamingResponse(
                    iter(
                        [
                            json.dumps(
                                {
                                    "type": "content",
                                    "content": "Invalid API Key. Please provide a valid API Key.",
                                }
                            )
                        ]
                    )
                )
            else:
                keyStatus = self.GetApiKeyStatus(keyId)
                if keyStatus == "DISABLED":
                    print(2)

                    return StreamingResponse(
                        iter(
                            [
                                json.dumps(
                                    {
                                        "type": "content",
                                        "content": "Your API Key is disabled. Please contact support.",
                                    }
                                )
                            ]
                        )
                    )

                elif keyStatus == "PENDING":
                    print(3)
                    return StreamingResponse(
                        iter(
                            [
                                json.dumps(
                                    {
                                        "type": "content",
                                        "content": "Your API Key is in processing data. Please wait for some time.",
                                    }
                                )
                            ]
                        )
                    )
                elif keyStatus == "ACTIVE":
                    tempKeyData = self.GetApiKeyData(keyId)
                    if tempKeyData == "ERROR":
                        print(4)

                        return StreamingResponse(
                            iter(
                                [
                                    json.dumps(
                                        {
                                            "type": "content",
                                            "content": "Sorry, Something went wrong !. Please Try again?",
                                        }
                                    )
                                ]
                            )
                        )
                    else:
                        keyData = tempKeyData

            chatMessages: list[ChatMessageModel] = [
                ChatMessageModel(
                    role=ChatMessageRoleEnum.SYSTEM,
                    content=CHATBOT_DEMO_PROMPT,
                ),
                ChatMessageModel(
                    role=ChatMessageRoleEnum.SYSTEM,
                    content=keyData,
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
            print("Hello")
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
            print(response)
            return response

        except Exception as e:
            print(e)
            return StreamingResponse(
                iter(
                    [
                        json.dumps(
                            {
                                "type": "content",
                                "content": "Sorry, Something went wrong !. Please Try again?",
                            }
                        )
                    ]
                )
            )
