from datetime import datetime, timezone
from pydantic import BaseModel, Field


def utcNow():
    return datetime.now(timezone.utc)


class TimeStampedModel(BaseModel):
    createdAt: datetime = Field(default_factory=utcNow)
    updatedAt: datetime = Field(default_factory=utcNow)


class DocumentsFileSchema(TimeStampedModel):
    id: str
    name: str
    mediaType: str
    data: str
    size: int
    content: str | None = None
    messageId: str
    chatId: str


class ChatSchema(TimeStampedModel):
    id: str
    summary: str
    emailId: str


class ChatMessageSchema(TimeStampedModel):
    id: str
    emailId: str
    chatId: str
    role: str
    content: str | None = None
    fileId: str | None = None
    reasoning: str | None = None
    toolName: str | None = None
