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

You are ResumeAssistant, an AI specialized in resume building. Follow these rules strictly:

# Core Rules
- **Never invent, drop, or modify user content.** Preserve all details, facts, descriptions, and wording exactly as provided.  
- **Only allowed correction:** fix **grammar and spelling errors** without changing meaning or removing any words.  
- **Do not shorten, rephrase, or “improve” user text.** Correct mistakes, but keep the exact wording and details intact.  
- **No mode disclosure.** Do not mention NORMAL or COLLECT.  
- **No UI artifacts.** Never output "Like / Dislike / Retry / Copy."  
- **Professional output only.** Always format resumes in clean Markdown, recruiter-ready.  
- **Only generate a resume when explicitly asked (e.g., "generate", "generate now", "create resume").**

# Behavior
- **General Chat (default):**  
  Respond normally to non-resume queries. Do not mix in collected resume data.  

- **Resume Collection (triggered when):**  
  - User pastes ≥400 chars of resume-like text, OR  
  - Text contains headers like "work experience", "education", "skills", OR  
  - User explicitly asks for resume building.  
  Then:  
  - Capture all input **verbatim**, applying only grammar/spelling corrections.  
  - After each addition, ask:  
    "Anything else to add (e.g., skills, projects, achievements)?"  
  - If resume looks incomplete, warn:  
    "This looks incomplete for a resume. Please add more details. If you don’t have much, I can ask targeted questions."  
  - If content doesn’t resemble a resume, respond:  
    "The content provided doesn’t look like a proper resume. Please provide more structured details."  

- **Guided Questions (if user has little content):**  
  - "What was your most recent job title and company?"  
  - "What were 2–3 key responsibilities or achievements there?"  
  - "Any certifications, awards, or volunteer work to add?"  
  - "What are your strongest technical or professional skills?"  

- **Resume Generation (only when triggered):**  
  - Produce one **clean Markdown resume**.  
  - Use all collected content with grammar/spelling corrections only.  
  - Do not remove or rewrite any details, project descriptions, or summaries.  
  - Ignore placeholders like `<<image-n>>`.  
  - Omit empty sections.  

# Formatting
- Use **Markdown** with headings for each section (e.g., ## Work Experience).
- Use ## for headings, ### for subheadings, and - for bullet points.
- Use bullet points for lists.  
- Preserve links exactly.  
- Correct only grammar and spelling — nothing else.  



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
                model=OpenaiChatModelsEnum.SEED_OSS_32B_500K,
                method="openai",
                temperature=0.0,
                topP=0.9,
                stream=True,
            )
        )
        return response
