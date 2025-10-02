from pydantic import BaseModel
from typing import List
from uuid import UUID


class ChatMessageModel(BaseModel):
    role: str
    id: UUID
    reasoningContent: str
    content: str


class FileModel(BaseModel):
    name: str
    mediaType: str
    data: str
    size: int


class ChatRequestModel(BaseModel):
    query: str
    messageId: str
    role: str
    useWebSearch: bool
    useDeepResearch: bool
    useFlash: bool
    messages: List[ChatMessageModel]
    files: list[FileModel] = []
