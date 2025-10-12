import asyncio
from app.implementations import ChatControllerServiceImpl
from app.models import ChatRequestModel, FileModel
from fastapi.responses import StreamingResponse, JSONResponse
from models import ChatRequestModel as ChatServiceRequestModel, ChatMessageModel
from enums import OpenaiChatModelsEnum, ChatMessageRoleEnum, CerebrasChatModelEnum
from services import ChatServices, DocServices
from app.utils import (
    CHAT_CONTROLLER_CHAT_PROMPT,
    CHAT_SUMMARY_PROMPT,
)
from database import chatMessagesCollection, chatsCollection,chatFilesCollection
from uuid import uuid4
from app.schemas import ChatFileSchema, ChatMessageSchema, ChatSchema
from app.ChatState import (
    ChatUsedTool,
    ChatEvent,
    ChatContent,
    ChatReasoning,
    ChatCompletionTokens,
    ChatPromptTokens,
    ChatTotalTokens,
    ReasoningTokens,
)
from typing import Any
import json
from app.WebSocketManager import webSocket
import time

from app.services.ApiKeyService import HandleKeyInterface
from app.utils import AppUtils


class ChatControllerServices(ChatControllerServiceImpl):
    def __init__(self):
        self.chatService = ChatServices()
        self.docService = DocServices()
        self.handleKeyInterface = HandleKeyInterface()
        self.appUtils = AppUtils()

    async def GenerateChatSummary(
        self,
        query: str,
        id: str,
        emailId: str,
        messagesLength: int,
        retryLimit: int = 0,
    ) -> None:
        if retryLimit >= 3:
            return
        messages: list[ChatMessageModel] = [
            ChatMessageModel(
                role=ChatMessageRoleEnum.SYSTEM,
                content=CHAT_SUMMARY_PROMPT,
            ),
            ChatMessageModel(
                role=ChatMessageRoleEnum.USER,
                content=query,
            ),
        ]
        try:
            response: Any = await self.chatService.Chat(
                modelParams=ChatServiceRequestModel(
                    messages=messages,
                    maxCompletionTokens=500,
                    model=CerebrasChatModelEnum.META_LLAMA_108B_INSTRUCT,
                    method="cerebras",
                    temperature=0.5,
                    topP=0.9,
                    stream=False,
                    responseFormat={
                        "type": "object",
                        "properties": {
                            "summary": {"type": "string"},
                            "generated": {"type": "string", "enum": ["true", "false"]},
                        },
                        "required": ["summary", "generated"],
                        "additionalProperties": False,
                    },
                )
            )
            chatResponse: dict[str, Any] = {}
            if response.content:
                try:
                    chatResponse = json.loads(response.content)
                except Exception as e:
                    await self.GenerateChatSummary(
                        query, id, emailId, messagesLength, retryLimit + 1
                    )
            title = chatResponse.get("response").get("summary", "")
            generated = chatResponse.get("response").get("generated", "")
            print(f"title: {title}, generated: {generated}")
            titleGenerated = generated == "true"

            await webSocket.sendToUser(
                email=emailId,
                message=json.dumps(
                    {
                        "type": (
                            "chatSummary"
                            if messagesLength == 0
                            else "chatSummaryUpdate"
                        ),
                        "title": title,
                        "chatId": id,
                        "titleGenerated": titleGenerated,
                    }
                ),
            )
            if title:
                self.SaveChat(
                    request=ChatSchema(
                        id=id,
                        title=title,
                        emailId=emailId,
                        titleGenerated=titleGenerated,
                    )
                )

        except Exception as e:
            print(e)
            time.sleep(3)
            await self.GenerateChatSummary(
                query, id, emailId, messagesLength, retryLimit + 1
            )

    async def Chat(self, request: ChatRequestModel) -> StreamingResponse:

        try:

            if request.titleGenerated is False:
                asyncio.create_task(
                    self.GenerateChatSummary(
                        query=request.query,
                        id=request.chatId,
                        emailId=request.emailId,
                        messagesLength=len(request.messages),
                    )
                )

            chatMessages: list[ChatMessageModel] = [
                ChatMessageModel(
                    role=ChatMessageRoleEnum.SYSTEM,
                    content=CHAT_CONTROLLER_CHAT_PROMPT,
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
                    maxCompletionTokens=30000,
                    model=OpenaiChatModelsEnum.QWEN_NEXT_80B_250K_INSTRUCT,
                    method="openai",
                    temperature=0.5,
                    topP=1.0,
                    stream=True,
                    tools=[
                        {
                            "type": "function",
                            "function": {
                                "name": "generatekey",
                                "description": "Generate a key based on user information if provided.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {},
                                    "required": [],
                                },
                            },
                        }
                    ],
                    messageId=request.messageId,
                )
            )

            async def CheckForToolExecution():
                await ChatEvent[request.messageId].wait()

                tempAssistentChatMessage = ChatMessageSchema(
                    id=str(uuid4()),
                    chatId=request.chatId,
                    role=ChatMessageRoleEnum.ASSISTANT.value,
                    content=ChatContent[request.messageId],
                    reasoning=ChatReasoning[request.messageId],
                    toolName=ChatUsedTool[request.messageId],
                )

                tempUserChatMessage = ChatMessageSchema(
                    id=request.messageId,
                    emailId=request.emailId,
                    chatId=request.chatId,
                    role=ChatMessageRoleEnum.USER.value,
                    content=request.query,
                )

                self.SaveChatMessage(tempUserChatMessage)
                self.SaveChatMessage(tempAssistentChatMessage)
                # if ChatUsedTool[request.messageId]:
                #     tempToolChatMessage = ChatMessageSchema(
                #         id=str(uuid4()),
                #         emailId=request.emailId,
                #         chatId=request.chatId,
                #         role=ChatMessageRoleEnum.ASSISTANT.value,
                #         content="Generated your key, you will get the key by email.",
                #     )
                #     self.SaveChatMessage(tempToolChatMessage)
                #     generatedKey = self.handleKeyInterface.GenerateKey()
                #     tempApiKeyId = str(uuid4())
                #     await self.GenerateChunkContent(
                #         messages=chatMessages,
                #         chatId=request.chatId,
                #         keyDetails=generatedKey,
                #         keyId=tempApiKeyId,
                #         retryLimit=0,
                #     )
                del ChatUsedTool[request.messageId]
                del ChatEvent[request.messageId]
                del ChatCompletionTokens[request.messageId]
                del ChatPromptTokens[request.messageId]
                del ChatTotalTokens[request.messageId]
                del ReasoningTokens[request.messageId]

            asyncio.create_task(CheckForToolExecution())

            return response

        except Exception as e:
            print(e)
            return StreamingResponse(
                iter([b"Sorry, Something went wrong !. Please Try again?"])
            )

    def SaveChatMessage(self, request: ChatMessageSchema, retryLimit: int = 0) -> None:
        try:
            chatMessagesCollection.insert_one(request.model_dump())
        except Exception as e:
            print(e)
            self.SaveChatMessage(request, retryLimit + 1) if retryLimit < 3 else None

    def SaveChat(
        self,
        request: ChatSchema,
        retryLimit: int = 0,
    ) -> None:
        try:
            chatsCollection.update_one(
                {"id": request.id}, {"$set": request.model_dump()}, upsert=True
            )
        except Exception as e:
            print(e)
            self.SaveChat(request, retryLimit + 1) if retryLimit < 3 else None

    def GetAllChats(self) -> JSONResponse:
        try:
            chats = list(chatsCollection.find({}).sort("createdAt", -1))
            tempAllChats: list[dict[str, str]] = []
            for chat in chats:
                tempAllChats.append(
                    {
                        "id": chat.get("id", ""),
                        "title": chat.get("title", ""),
                        "titleGenerated": chat.get("titleGenerated", False),
                    }
                )
            return JSONResponse(
                status_code=200,
                content={"data": "SUCCESS", "allChats": tempAllChats},
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

    def getChatHistory(self, id: str) -> JSONResponse:
        try:
            chatDetails = chatsCollection.find_one({"id": id})

            chatsMessages = list(chatMessagesCollection.find({"chatId": id}))
            tempChatHistory: list[dict[str, str]] = []
            for chat in chatsMessages:
                tempChatHistory.append(
                    {
                        "id": chat.get("id", ""),
                        "role": chat.get("role", "").lower(),
                        "content": chat.get("content", ""),
                        "visible": chat.get("visible", ""),
                        "liked": chat.get("liked", ""),
                        "disLiked": chat.get("disLiked", ""),
                        "timeAndDate": str(chat.get("createdAt", "")),
                    }
                )
            return JSONResponse(
                status_code=200,
                content={
                    "data": "SUCCESS",
                    "chatHistory": tempChatHistory,
                    "titleGenerated": (chatDetails.get("titleGenerated", False)),
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

    def DeleteChat(self, id: str) -> JSONResponse:
        try:
            chatsCollection.delete_one({"id": id})
            chatMessagesCollection.delete_many({"chatId": id})

            return JSONResponse(
                status_code=200,
                content={"data": "SUCCESS", "id": id},
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

    async def UploadFile(self, request: FileModel, retryLimit: int = 0) -> JSONResponse:
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

            dbSchema = ChatFileSchema(
                name=request.name,
                mediaType=request.mediaType,
                data=request.data,
                size=request.size,
                id=str(fileId),
                content=text,
                messageId=request.messageId if request.messageId else str(uuid4()),
                chatId=request.chatId if request.chatId else str(uuid4()),
                tokensCount=tokensCount,
            )

            self.SaveChatMessage(
                request=ChatMessageSchema(
                    id=request.messageId if request.messageId else str(uuid4()),
                    chatId=request.chatId if request.chatId else str(uuid4()),
                    role=ChatMessageRoleEnum.USER.value,
                    content=f"File name: {request.name}\n File Size:{request.size} File type:{request.mediaType} Extracted Text: {text}",
                    emailId=request.emailId,
                    visible=False,
                    fileId=str(fileId),
                )
            )
            chatFilesCollection.insert_one(dbSchema.model_dump())
            return JSONResponse(
                status_code=200,
                content={
                    "data": "SUCCESS",
                    "id": str(fileId),
                    "text": f"File name: {request.name}\n File Size:{request.size} File type:{request.mediaType} Extracted Text: {text[1:100]}...",
                },
            )
        except Exception as e:
            print(e)
            if retryLimit < 3:
                return await self.UploadFile(request, retryLimit + 1)
            return JSONResponse(
                status_code=500,
                content={
                    "data": "ERROR",
                    "error": str(e),
                },
            )

    