from pydantic import BaseModel


class QaCsvChunksResponseModel(BaseModel):
    questions: list[str]
    answers: list[str]



class YtVideoChunksResponseModel(BaseModel):
    videoId: str
    chunkText: str
    chunkUrl: str