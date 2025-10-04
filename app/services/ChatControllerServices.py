import asyncio
from app.implementations import ChatControllerServiceImpl
from app.models import ChatRequestModel, FileModel
from fastapi.responses import StreamingResponse, JSONResponse
from models import ChatRequestModel as ChatServiceRequestModel, ChatMessageModel
from enums import OpenaiChatModelsEnum, ChatMessageRoleEnum, CerebrasChatModelEnum
from services import ChatServices, DocServices
from app.utils import (
    CHAT_CONTROLLER_CHAT_PROMPT,
    GENERATE_RESUME_PROMPT,
    CHAT_SUMMARY_PROMPT,
)
from database import mongoClient
from uuid import uuid4
from app.schemas import DocumentsFileSchema, ChatMessageSchema, ChatSchema
from app.state import ChatUsedTool, ChatEvent, chatContent, chatReasoning
from typing import Any
import json
from app.WebSocketManager import webSocket


chatService = ChatServices()
docService = DocServices()
db = mongoClient["aifolio"]


class ChatControllerServices(ChatControllerServiceImpl):

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
            response: Any = await chatService.Chat(
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
            titleGenerated = generated == "true"

            if messagesLength == 0 or titleGenerated:
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
            await self.GenerateChatSummary(
                query, id, emailId, messagesLength, retryLimit + 1
            )

    async def Chat(self, request: ChatRequestModel) -> StreamingResponse:

        try:
            fileData = ""
            if request.fileId:
                fileData = self.GetFileContent(request.fileId)

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
                    content=(
                        (fileData + "\n\n" + request.query)
                        if getattr(request, "fileId", None)
                        else request.query
                    ),
                ),
            ]

            response: Any = await chatService.Chat(
                modelParams=ChatServiceRequestModel(
                    messages=chatMessages,
                    maxCompletionTokens=20000,
                    model=OpenaiChatModelsEnum.GPT_OSS_120B_110K,
                    method="openai",
                    temperature=0.5,
                    topP=0.9,
                    stream=True,
                    tools=[
                        {
                            "type": "function",
                            "function": {
                                "name": "generate_resume",
                                "description": "Generate a canonical resume from stored user content (server-side).",
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
                    content=chatContent[request.messageId],
                    reasoning=chatReasoning[request.messageId],
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
                if ChatUsedTool[request.messageId]:
                    await self.GenerateResumeContent(messages=chatMessages)
                del ChatUsedTool[request.messageId]
                del ChatEvent[request.messageId]

            asyncio.create_task(CheckForToolExecution())

            return response

        except Exception as e:
            print(e)
            return StreamingResponse(
                iter([b"Sorry, Something went wrong !. Please Try again?"])
            )

    def SaveChatMessage(self, request: ChatMessageSchema, retryLimit: int = 0) -> None:
        try:
            collection = db["chatMessages"]
            collection.insert_one(request.model_dump())
        except Exception as e:
            print(e)
            self.SaveChatMessage(request, retryLimit + 1) if retryLimit < 3 else None

    def SaveChat(
        self,
        request: ChatSchema,
        retryLimit: int = 0,
    ) -> None:
        try:
            collection = db["chats"]
            collection.update_one(
                {"id": request.id}, {"$set": request.model_dump()}, upsert=True
            )
        except Exception as e:
            print(e)
            self.SaveChat(request, retryLimit + 1) if retryLimit < 3 else None

    def GetFileContent(self, fileId: str) -> str:
        collection = db["files"]
        fileData = collection.find_one({"id": fileId})
        if fileData:
            return fileData.get("content", "")
        return ""

    def GetAllChats(self) -> JSONResponse:
        try:
            collection = db["chats"]
            chats = list(collection.find({}).sort("createdAt", -1))
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
            collection = db["chatMessages"]
            chats = list(collection.find({"chatId": id}))
            tempChatHistory: list[dict[str, str]] = []
            for chat in chats:
                tempChatHistory.append(
                    {
                        "id": chat.get("id", ""),
                        "role": chat.get("role", "").lower(),
                        "content": chat.get("content", ""),
                    }
                )
            return JSONResponse(
                status_code=200,
                content={"data": "SUCCESS", "chatHistory": tempChatHistory},
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
            chatCollection = db["chats"]
            chatMessageCollection = db["chatMessages"]
            chatCollection.delete_one({"id": id})
            chatMessageCollection.delete_many({"chatId": id})

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
            text, _ = docService.ExtractTextAndImagesFromPdf(request.data)

            dbSchema = DocumentsFileSchema(
                name=request.name,
                mediaType=request.mediaType,
                data=request.data,
                size=request.size,
                id=str(fileId),
                content=text,
                messageId=request.messageId,
                chatId=request.chatId,
            )

            collection = db["files"]
            collection.insert_one(dbSchema.model_dump())
            return JSONResponse(
                status_code=200,
                content={
                    "data": "SUCCESS",
                    "id": str(fileId),
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

    async def GenerateResumeContent(self, messages: list[ChatMessageModel]):
        messages.pop(0)
        messages.append(
            ChatMessageModel(
                role=ChatMessageRoleEnum.SYSTEM,
                content=GENERATE_RESUME_PROMPT,
            )
        )
        response = await chatService.Chat(
            modelParams=ChatServiceRequestModel(
                messages=messages,
                maxCompletionTokens=8000,
                model=CerebrasChatModelEnum.GPT_OSS_120B,
                method="cerebras",
                temperature=0.1,
                topP=0.9,
                stream=False,
                responseFormat={
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string"},
                    },
                    "required": ["summary"],
                    "additionalProperties": False,
                },
            )
        )
