from datetime import datetime, timezone
from pydantic import BaseModel, Field


def utcNow():
    return datetime.now(timezone.utc)


class TimeStampedModel(BaseModel):
    createdAt: datetime = Field(default_factory=utcNow)
    updatedAt: datetime = Field(default_factory=utcNow)


class ChatFileSchema(TimeStampedModel):
    id: str
    name: str
    mediaType: str
    data: str
    size: int
    type: str = "chat"
    content: str | None = None
    messageId: str
    chatId: str
    tokensCount: int | None = 0
    type: str = "CONTEXT"


class ApiKeyFileSchema(TimeStampedModel):
    id: str
    name: str
    mediaType: str
    data: str
    size: int
    type: str = "context"
    tokensCount: int | None = 0
    fileUrl: str | None = None
    content: str | None = None


class ChatSchema(TimeStampedModel):
    id: str
    title: str
    emailId: str
    titleGenerated: bool = False


class ChatMessageSchema(TimeStampedModel):
    id: str
    emailId: str | None = None
    chatId: str
    role: str
    content: str | None = None
    fileId: str | None = None
    reasoning: str | None = None
    toolName: str | None = None
    visible: bool = True
    liked: bool | None = False
    disLiked: bool | None = False


class ApiKeySchema(TimeStampedModel):
    id: str
    pdfFileIds: list[str] | None = None
    csvFileIds: list[str] | None = None
    txtFileIds: list[str] | None = None
    ytVideoFileIds: list[str] | None = None
    name: str
    key: str
    hash: str
    salt: bytes
    status: str = "PENDING"
    disabled: bool = False
    deleted: bool = False
    filesType: str = "SINGLE"
    singleFileId: str | None = None
    methodType: str = "CONTEXT"


class ApiKeyDataSchema(TimeStampedModel):
    id: str
    apiKeyId: str
    data: str
