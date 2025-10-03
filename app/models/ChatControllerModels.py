from pydantic import BaseModel
from typing import List
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
    chatId: str
    messageId: str


class ChatRequestModel(BaseModel):
    messageId: str
    chatId: str 
    query: str
    role: str
    useWebSearch: bool
    useDeepResearch: bool
    useFlash: bool
    messages: List[ChatMessageModel]
    fileId: str | None = None
    emailId:str
