import asyncio
from app.implementations import ChatControllerServiceImpl
from app.models import ChatRequestModel, FileModel
from fastapi.responses import StreamingResponse, JSONResponse
from models import ChatRequestModel as ChatServiceRequestModel, ChatMessageModel
from enums import OpenaiChatModelsEnum, ChatMessageRoleEnum, CerebrasChatModelEnum
from services import ChatServices, DocServices
from app.utils import CHAT_CONTROLLER_CHAT_PROMPT
from database import mongoClient
from uuid import uuid4
from app.state import chatDetectedTools, chatCompletionEvents

chatService = ChatServices()
docService = DocServices()


class ChatControllerServices(ChatControllerServiceImpl):

    async def UploadFile(self, request: FileModel) -> JSONResponse:
        try:
            text, _ = docService.ExtractTextAndImagesFromPdf(request.data)
            db = mongoClient["documents"]
            collection = db["files"]
            request.text = text
            response = collection.insert_one(request.model_dump())

            return JSONResponse(
                status_code=200,
                content={
                    "data": "SUCCESS",
                    "id": str(response.inserted_id),
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
                content="""
                # Output Schema
                - When generating the final response (resume or otherwise), always wrap it in the following JSON structure:

                {
                "response": {
                    "summary": "..."
                }
                }

                - Replace the value of "summary" with the actual resume or message content.
                - Do not output anything outside this JSON object
                - Do not remove or rewrite any details, project descriptions, or summaries.
                - Use all collected content with grammar/spelling corrections only.
                - Read all chat for any updates in resume content. 
                 

                """,
            )
        )

        response = await chatService.Chat(
            modelParams=ChatServiceRequestModel(
                messages=messages,
                maxCompletionTokens=20000,
                model=CerebrasChatModelEnum.QWEN_235B,
                method="openai",
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
        print(response)

    async def Chat(self, request: ChatRequestModel) -> StreamingResponse:

        chatMessage: list[ChatMessageModel] = [
            ChatMessageModel(
                role=ChatMessageRoleEnum.SYSTEM,
                content=CHAT_CONTROLLER_CHAT_PROMPT,
            )
        ]
        for msg in request.messages:
            chatMessage.append(
                ChatMessageModel(
                    role=(
                        ChatMessageRoleEnum.USER
                        if msg.role == "user"
                        else ChatMessageRoleEnum.ASSISTANT
                    ),
                    content=msg.content,
                )
            )

        if len(request.files) > 0:
            for file in request.files:
                text, _ = docService.ExtractTextAndImagesFromPdf(file.data)
                chatMessage.append(
                    ChatMessageModel(
                        role=ChatMessageRoleEnum.USER,
                        content=text + request.query,
                    )
                )
        else:
            chatMessage.append(
                ChatMessageModel(
                    role=ChatMessageRoleEnum.USER,
                    content=request.query,
                )
            )
        requestId = uuid4()

        response = await chatService.Chat(
            modelParams=ChatServiceRequestModel(
                messages=chatMessage,
                maxCompletionTokens=20000,
                model=CerebrasChatModelEnum.GPT_OSS_120B,
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
                requestId=requestId,
            )
        )

        async def CheckForToolExecution():
            await chatCompletionEvents[requestId].wait()
            if chatDetectedTools[requestId]:
                await self.GenerateResumeContent(messages=chatMessage)
            del chatDetectedTools[requestId]
            del chatCompletionEvents[requestId]

        asyncio.create_task(CheckForToolExecution())

        return response
