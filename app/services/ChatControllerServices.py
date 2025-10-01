from app.implementations import ChatControllerServiceImpl
from app.models import ChatRequestModel
from fastapi.responses import StreamingResponse
from models import ChatRequestModel as ChatServiceRequestModel, ChatMessageModel
from enums import OpenaiChatModelsEnum, ChatMessageRoleEnum
from services import ChatServices, DocServices


chatService = ChatServices()
docService = DocServices()


class ChatControllerServices(ChatControllerServiceImpl):

    async def Chat(self, request: ChatRequestModel) -> StreamingResponse:

        text, _ = docService.ExtractTextAndImagesFromPdf("resume.pdf")

        chatMessage: list[ChatMessageModel] = [
            ChatMessageModel(
                role=ChatMessageRoleEnum.SYSTEM,
                content="""
You are ResumeAssistant. Start in NORMAL mode (general chat). Switch to COLLECT mode when user pastes/uploads resume-like content (>=400 chars or contains headers like work experience/education/skills) or explicitly requests resume building. In COLLECT mode: capture and show all content verbatim (append-only), never rewrite or invent facts, ask "Anything else to add?" after each addition. If content is too short or missing essentials, warn: "This looks incomplete for a resume. Please add more details... If you don't have much, tell me — I'll ask targeted questions." Use guided questions when the user says they lack details. Only generate the resume when the user types a trigger (generate/generate now/create resume/etc.). On generation, produce one clean resume using ONLY collected content, preserving all details and full project descriptions. Never include UI artifacts or invented content.




""",
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

        if request.file:
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
                model=OpenaiChatModelsEnum.QWEN_NEXT_80B_200K,
                method="openai",
                temperature=0.7,
                topP=0.9,
                stream=True,
            )
        )
        return response
