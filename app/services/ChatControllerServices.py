from app.implementations import ChatControllerServiceImpl
from app.models import ChatRequestModel
from fastapi.responses import StreamingResponse
from models import ChatRequestModel as ChatServiceRequestModel, ChatMessageModel
from enums import OpenaiChatModelsEnum, ChatMessageRoleEnum
from services import ChatServices, DocServices
from app.utils import CHAT_CONTROLLER_CHAT_PROMPT


chatService = ChatServices()
docService = DocServices()


class ChatControllerServices(ChatControllerServiceImpl):

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

        response = await chatService.Chat(
            modelParams=ChatServiceRequestModel(
                messages=chatMessage,
                maxCompletionTokens=20000,
                model=OpenaiChatModelsEnum.SEED_OSS_32B_500K,
                method="openai",
                temperature=0.0,
                topP=0.9,
                stream=True,
            )
        )
        return response
