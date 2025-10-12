from abc import ABC, abstractmethod
from models import (
    AllChunksWithQuestionsModel,
    QaCsvChunksResponseModel,
    ChatMessageModel,
    ExtractQaFromChunkResponseModel,
)
from typing import Tuple


class RagServicesImpl(ABC):

    @abstractmethod
    async def ExtractQuestionAndAnswersFromPdfFile(
        self, file: str
    ) -> AllChunksWithQuestionsModel:
        pass

    @abstractmethod
    async def ExtractQuestionsAndAnswersFromCsvFile(
        self, file: str
    ) -> AllChunksWithQuestionsModel:
        pass

    @abstractmethod
    async def ExtractQuestionAndAnswersFromYtVideo(
        self, videoId: str
    ) -> AllChunksWithQuestionsModel:
        pass


class ChunkServicesImpl(ABC):

    @abstractmethod
    def GenerateShortId(self, length: int = 8) -> str:
        pass

    @abstractmethod
    def ExtractChunkFromPdfText(
        self, file: str, chunkSize: int, chunkOLSize: int | None = 0
    ) -> Tuple[list[str], list[str]]:
        pass

    @abstractmethod
    def ExtractChunksFromPdf(self, file: str) -> list[str]:
        pass

    @abstractmethod
    def ExtractQuestionsAndAnswersFromCsvFile(
        self, file: str
    ) -> QaCsvChunksResponseModel:
        pass


class ExtractInstanceServiceImpl(ABC):

    @abstractmethod
    async def ExtractQuestionsFromChunk(
        self,
        messages: list[ChatMessageModel],
        retryLimit: int,
    ) -> ExtractQaFromChunkResponseModel:
        pass

    @abstractmethod
    async def CleanYoutubeChunk(
        self,
        messages: list[ChatMessageModel],
        retryLimit: int,
    ) -> str:
        pass
