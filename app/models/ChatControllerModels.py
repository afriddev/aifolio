from pydantic import BaseModel
from uuid import UUID


class ChatMessageModel(BaseModel):
    role: str
    id: UUID
    reasoningContent: str | None = None
    content: str


class FileModel(BaseModel):
    name: str
    mediaType: str
    data: str
    size: int
    chatId: str | None = None
    messageId: str | None = None
    emailId: str


class ChatRequestModel(BaseModel):
    messageId: str
    chatId: str
    query: str
    role: str
    useWebSearch: bool
    useThink: bool
    useFlash: bool
    messages: list[ChatMessageModel]
    fileId: str | None = None
    emailId: str
    titleGenerated: bool | None = False

class DeleteChatRequestModel(BaseModel):
    id: str
    
    
class PreProcessUserQueryResponseModel(BaseModel):
    cleanQuery: str
    type:str