from pydantic import BaseModel
from uuid import UUID


class ExtractQaFromChunkResponseModel(BaseModel):
    questions: list[str]
    chunk: str


class QaChunkModel(BaseModel):
    id: UUID
    text: str


class QaQuestionsModel(BaseModel):
    id: UUID
    chunkId: UUID
    text: str
