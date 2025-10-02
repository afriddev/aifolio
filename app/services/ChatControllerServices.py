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
from app.schemas import DocumentsFIleSchema
from app.state import ChatUsedTool, ChatEvent, chatContent, chatReasoning
from typing import Any

chatService = ChatServices()
docService = DocServices()
db = mongoClient["aifolio"]


class ChatControllerServices(ChatControllerServiceImpl):

    async def GenerateChatSummary(self, query: str):
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
        response = await chatService.Chat(
            modelParams=ChatServiceRequestModel(
                messages=messages,
                maxCompletionTokens=500,
                model=CerebrasChatModelEnum.META_LLAMA_17B_MAVERICK,
                method="cerebras",
                temperature=0.7,
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
        print(response)

    async def Chat(self, request: ChatRequestModel) -> StreamingResponse:

        try:
            fileData = ""
            if request.fileId:
                fileData = self.GetFileContent(request.fileId)

            if len(request.messages) == 0:
                asyncio.create_task(self.GenerateChatSummary(request.query))

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
                    model=OpenaiChatModelsEnum.SEED_OSS_32B_500K,
                    method="openai",
                    temperature=0.3,
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
                # print(chatContent[request.messageId])
                # print(chatReasoning[request.messageId])
                # print(ChatUsedTool[request.messageId])
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

    def GetFileContent(self, fileId: str) -> str:
        collection = db["files"]
        fileData = collection.find_one({"id": fileId})
        if fileData:
            return fileData.get("content", "")
        return ""

    async def UploadFile(self, request: FileModel) -> JSONResponse:
        try:
            fileId = uuid4()
            text, _ = docService.ExtractTextAndImagesFromPdf(request.data)

            dbSchema = DocumentsFIleSchema(
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
                maxCompletionTokens=20000,
                model=CerebrasChatModelEnum.QWEN_235B,
                method="cerebras",
                temperature=0.0,
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
