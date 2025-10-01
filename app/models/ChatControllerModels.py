from pydantic import BaseModel
from typing import List
from uuid import UUID


class Message(BaseModel):
    role: str
    id: UUID
    reasoningContent: str
    content: str


# Main model for the form data
class ChatRequestModel(BaseModel):
    query: str
    messageId: str
    role: str
    useWebSearch: bool
    useDeepResearch: bool
    useFlash: bool
    messages: List[Message]
    file: bool = False
