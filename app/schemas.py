from pydantic import BaseModel


class DocumentsFIleSchema(BaseModel):
    name: str
    mediaType: str
    data: str
    size: int
    content: str | None = None
    id: str
    messageId: str
    chatId: str


class ChatSchema(BaseModel):
    id: str | None = None
    summary: str | None = None


class ChatMessageSchema(BaseModel):
    role: str
    content: str
    reasoning: str | None = None
    tool: str | None = None
    id: str | None = None
    chatId: str | None = None
    messageId: str | None = None
